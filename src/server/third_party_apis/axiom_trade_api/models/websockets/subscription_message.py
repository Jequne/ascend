from pydantic import BaseModel, Field, ConfigDict, model_validator, model_serializer
from typing import Optional, Dict, List, Literal
from datetime import datetime, timedelta
import time


class BaseSubscribeMessage(BaseModel):
    action: str = "join"
    room: Literal["new_pairs", "sol_price", "migrations"]