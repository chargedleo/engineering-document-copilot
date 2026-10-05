import logging
from typing import Optional, Dict, Any, Union

logger = logging.getLogger("engineering_copilot.agents.tools.calculator")

BAR_TO_PSI_FACTOR = 14.50377377
KW_TO_HP_FACTOR = 1.34102209


class EngineeringCalculatorTool:
    """
    Safe, deterministic engineering calculation tool.
    Never uses eval(). Performs explicit, validated engineering conversions
    and formula evaluations (pressure, temperature, flow rate, power, percentage changes).
    """
    name: str = "calculate_engineering"
    description: str = (
        "Perform deterministic engineering calculations and unit conversions. "
        "Supported operations: 'bar_to_psi', 'psi_to_bar', 'celsius_to_fahrenheit', "
        "'fahrenheit_to_celsius', 'percentage_change', 'flow_m3h_to_lpm', 'flow_lpm_to_m3h', "
        "'kw_to_hp', 'hp_to_kw'."
    )

    SUPPORTED_OPERATIONS = {
        "bar_to_psi": "Convert bar gauge/absolute to pounds per square inch (psi)",
        "psi_to_bar": "Convert pounds per square inch (psi) to bar",
        "celsius_to_fahrenheit": "Convert Celsius (°C) to Fahrenheit (°F)",
        "fahrenheit_to_celsius": "Convert Fahrenheit (°F) to Celsius (°C)",
        "percentage_change": "Calculate percentage delta between baseline value and final value",
        "flow_m3h_to_lpm": "Convert volumetric flow from m³/h to Liters/minute (L/min)",
        "flow_lpm_to_m3h": "Convert volumetric flow from Liters/minute (L/min) to m³/h",
        "kw_to_hp": "Convert power from kilowatts (kW) to horsepower (hp)",
        "hp_to_kw": "Convert power from horsepower (hp) to kilowatts (kW)",
    }

    @classmethod
    def run(
        cls,
        operation: str,
        value: Union[int, float],
        value2: Optional[Union[int, float]] = None,
    ) -> Dict[str, Any]:
        """Execute a deterministic engineering calculation."""
        op_norm = operation.strip().lower()

        if op_norm not in cls.SUPPORTED_OPERATIONS:
            return {
                "success": False,
                "error": f"Unsupported calculation operation '{operation}'. Supported operations: {list(cls.SUPPORTED_OPERATIONS.keys())}",
                "operation": operation,
            }

        try:
            val_float = float(value)
        except (ValueError, TypeError):
            return {
                "success": False,
                "error": f"Invalid numerical value: {value}",
                "operation": operation,
            }

        if op_norm == "bar_to_psi":
            result = round(val_float * BAR_TO_PSI_FACTOR, 2)
            unit = "psi"
            explanation = f"{val_float} bar * 14.50377 psi/bar ~= {result} psi"

        elif op_norm == "psi_to_bar":
            result = round(val_float / BAR_TO_PSI_FACTOR, 4)
            unit = "bar"
            explanation = f"{val_float} psi / 14.50377 psi/bar ~= {result} bar"

        elif op_norm == "celsius_to_fahrenheit":
            result = round((val_float * 9.0 / 5.0) + 32.0, 2)
            unit = "deg F"
            explanation = f"({val_float} deg C * 9/5) + 32 = {result} deg F"

        elif op_norm == "fahrenheit_to_celsius":
            result = round((val_float - 32.0) * 5.0 / 9.0, 2)
            unit = "deg C"
            explanation = f"({val_float} deg F - 32) * 5/9 = {result} deg C"

        elif op_norm == "flow_m3h_to_lpm":
            result = round((val_float * 1000.0) / 60.0, 2)
            unit = "L/min"
            explanation = f"({val_float} m3/h * 1000) / 60 = {result} L/min"

        elif op_norm == "flow_lpm_to_m3h":
            result = round((val_float * 60.0) / 1000.0, 4)
            unit = "m3/h"
            explanation = f"({val_float} L/min * 60) / 1000 = {result} m3/h"

        elif op_norm == "kw_to_hp":
            result = round(val_float * KW_TO_HP_FACTOR, 2)
            unit = "hp"
            explanation = f"{val_float} kW * 1.34102 = {result} hp"

        elif op_norm == "hp_to_kw":
            result = round(val_float / KW_TO_HP_FACTOR, 2)
            unit = "kW"
            explanation = f"{val_float} hp / 1.34102 = {result} kW"

        elif op_norm == "percentage_change":
            if value2 is None:
                return {
                    "success": False,
                    "error": "Operation 'percentage_change' requires 'value2' (comparison value).",
                    "operation": operation,
                }
            try:
                v2_float = float(value2)
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "error": f"Invalid second numerical value: {value2}",
                    "operation": operation,
                }
            if val_float == 0.0:
                return {
                    "success": False,
                    "error": "Cannot compute percentage change with baseline value of 0.",
                    "operation": operation,
                }
            delta = v2_float - val_float
            result = round((delta / val_float) * 100.0, 2)
            unit = "%"
            explanation = f"(({v2_float} - {val_float}) / {val_float}) * 100% = {result:+}%"

        else:
            return {
                "success": False,
                "error": f"Unhandled operation: {op_norm}",
                "operation": operation,
            }

        return {
            "success": True,
            "operation": op_norm,
            "input": val_float,
            "result": result,
            "unit": unit,
            "explanation": explanation,
        }
