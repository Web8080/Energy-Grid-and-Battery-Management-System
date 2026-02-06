"""
Schedule Executor

Handles actual battery command execution on the Raspberry Pi.
This module interfaces with hardware controllers to execute
charge/discharge commands.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ScheduleExecutor:
    """
    Executes battery charge/discharge commands.
    
    In production, this would interface with actual hardware controllers.
    This implementation simulates command execution for development/testing.
    """
    
    def __init__(self, device_id: str):
        """
        Initialize the executor.
        
        Args:
            device_id: Device identifier
        """
        self.device_id = device_id
    
    async def execute_command(
        self,
        mode: int,
        rate_kw: float
    ) -> Tuple[bool, Optional[float]]:
        """
        Execute a charge or discharge command.
        
        Args:
            mode: 1 for discharge, 2 for charge
            rate_kw: Target rate in kW
        
        Returns:
            Tuple of (success, actual_rate_kw)
        """
        logger.info(
            f"Executing command: device={self.device_id}, "
            f"mode={mode}, rate={rate_kw}kW"
        )
        
        try:
            if mode == 1:
                actual_rate = await self._execute_discharge(rate_kw)
            elif mode == 2:
                actual_rate = await self._execute_charge(rate_kw)
            else:
                raise ValueError(f"Invalid mode: {mode}")
            
            logger.info(
                f"Command executed successfully: "
                f"target={rate_kw}kW, actual={actual_rate}kW"
            )
            
            return True, actual_rate
        
        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            return False, None
    
    async def _execute_discharge(self, rate_kw: float) -> float:
        """
        Execute discharge command.
        
        Args:
            rate_kw: Target discharge rate
        
        Returns:
            Actual discharge rate achieved
        """
        logger.debug(f"Discharging at {rate_kw}kW")
        
        actual_rate = rate_kw * 0.98
        
        return actual_rate
    
    async def _execute_charge(self, rate_kw: float) -> float:
        """
        Execute charge command.
        
        Args:
            rate_kw: Target charge rate
        
        Returns:
            Actual charge rate achieved
        """
        logger.debug(f"Charging at {rate_kw}kW")
        
        actual_rate = rate_kw * 0.97
        
        return actual_rate
