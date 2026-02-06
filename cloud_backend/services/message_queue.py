"""
Message Queue Service

RabbitMQ integration for async message processing and device communication.
Handles schedule distribution via MQTT and acknowledgement processing.
"""

import json
import logging
from typing import Callable, Optional

import pika
from pika.adapters.blocking_connection import BlockingConnection
from pika.connection import URLParameters

logger = logging.getLogger(__name__)


class MessageQueueService:
    """
    Service for RabbitMQ message queue operations.
    
    Handles publishing and consuming messages for schedule distribution
    and device acknowledgement processing.
    """
    
    def __init__(self, rabbitmq_url: str, exchange: str = "energy_grid"):
        """
        Initialize message queue service.
        
        Args:
            rabbitmq_url: RabbitMQ connection URL
            exchange: Exchange name for routing
        """
        self.rabbitmq_url = rabbitmq_url
        self.exchange = exchange
        self.connection: Optional[BlockingConnection] = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            parameters = URLParameters(self.rabbitmq_url)
            self.connection = BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type="topic",
                durable=True
            )
            
            logger.info(f"Connected to RabbitMQ: {self.exchange}")
        
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
            raise
    
    def disconnect(self):
        """Close RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Disconnected from RabbitMQ")
    
    def publish_schedule(
        self,
        device_id: str,
        schedule: list,
        routing_key: Optional[str] = None
    ):
        """
        Publish schedule to device via message queue.
        
        Args:
            device_id: Device identifier
            schedule: Schedule entries
            routing_key: Optional routing key (defaults to device-specific)
        """
        if not self.channel:
            self.connect()
        
        message = {
            "device_id": device_id,
            "schedule": schedule,
            "timestamp": json.dumps(datetime.utcnow().isoformat())
        }
        
        routing_key = routing_key or f"devices.{device_id}.schedule.response"
        
        try:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )
            
            logger.info(f"Published schedule to {device_id} via {routing_key}")
        
        except Exception as e:
            logger.error(f"Failed to publish schedule: {e}", exc_info=True)
            raise
    
    def consume_acknowledgements(
        self,
        callback: Callable,
        queue_name: str = "device.acks"
    ):
        """
        Consume device acknowledgements from queue.
        
        Args:
            callback: Function to process acknowledgements
            queue_name: Queue name for acknowledgements
        """
        if not self.channel:
            self.connect()
        
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        self.channel.queue_bind(
            exchange=self.exchange,
            queue=queue_name,
            routing_key="devices.*.ack"
        )
        
        def on_message(ch, method, properties, body):
            try:
                ack_data = json.loads(body)
                callback(ack_data)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing acknowledgement: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message
        )
        
        logger.info(f"Started consuming acknowledgements from {queue_name}")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            logger.info("Stopped consuming acknowledgements")


from datetime import datetime
