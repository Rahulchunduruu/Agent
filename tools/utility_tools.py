"""Utility tools: get_datetime, calculator, get_weather."""

import ast
import math
from datetime import datetime

import requests
from langchain_core.tools import tool

from config import Config


@tool
def get_datetime() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculator(expression: str) -> str:
    """Safely evaluate arithmetic expressions and common math functions. Supports +, -, *, /, %, //, **, parentheses, decimals, and functions like sqrt, sin, cos, tan, log, log10, abs, floor, ceil, factorial."""
    try:
        cleaned = (expression or "").strip().replace("^", "**")
        if not cleaned:
            return "Error: Please provide a math expression."

        allowed_functions = {
            "abs": abs,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "floor": math.floor,
            "ceil": math.ceil,
            "factorial": math.factorial,
            "pow": pow,
        }

        allowed_names = {"pi": math.pi, "e": math.e}
        tree = ast.parse(cleaned, mode="eval")

        def _eval(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.Name):
                if node.id in allowed_names:
                    return allowed_names[node.id]
                raise ValueError(f"Unsupported name: {node.id}")
            if isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, ast.Div):
                    return left / right
                if isinstance(node.op, ast.FloorDiv):
                    return left // right
                if isinstance(node.op, ast.Mod):
                    return left % right
                if isinstance(node.op, ast.Pow):
                    return left ** right
                raise ValueError("Unsupported operator")
            if isinstance(node, ast.UnaryOp):
                value = _eval(node.operand)
                if isinstance(node.op, ast.UAdd):
                    return +value
                if isinstance(node.op, ast.USub):
                    return -value
                raise ValueError("Unsupported unary operator")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name not in allowed_functions:
                    raise ValueError(f"Unsupported function: {func_name}")
                args = [_eval(arg) for arg in node.args]
                if func_name in {"abs", "sqrt", "sin", "cos", "tan", "log", "log10", "floor", "ceil", "factorial"}:
                    if len(args) != 1:
                        raise ValueError(f"{func_name} expects exactly one argument")
                if func_name == "pow":
                    if len(args) != 2:
                        raise ValueError("pow expects exactly two arguments")
                return allowed_functions[func_name](*args)
            raise ValueError("Unsupported expression")

        result = _eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_weather(city: str = "Guntur", country: str = "India") -> str:
    """Get current weather for health-related queries like heatstroke,
    seasonal allergies, humidity-related illness, cold weather precautions.
    city: Name of the city
    country: Name of the country
    """
    try:
        API_KEY = Config.OPENWEATHER_API_KEY

        weather_url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={city},{country}&appid={API_KEY}&units=metric"
        )
        weather = requests.get(weather_url).json()

        if str(weather.get("cod")) != "200":
            return f"City not found: {weather.get('message', 'Unknown error')}"

        lat = weather["coord"]["lat"]
        lon = weather["coord"]["lon"]

        aqi_url = (
            f"http://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={API_KEY}"
        )
        aqi_res = requests.get(aqi_url).json()
        aqi_index = aqi_res["list"][0]["main"]["aqi"]
        aqi_level = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}

        return (
            f"City: {weather['name']}, {country} | "
            f"Temp: {weather['main']['temp']}°C | "
            f"Feels Like: {weather['main']['feels_like']}°C | "
            f"Humidity: {weather['main']['humidity']}% | "
            f"Condition: {weather['weather'][0]['description'].title()} | "
            f"Wind: {weather['wind']['speed']} m/s | "
            f"AQI: {aqi_level.get(aqi_index, 'Unknown')}"
        )

    except Exception as e:
        return f"Weather unavailable: {str(e)}"
