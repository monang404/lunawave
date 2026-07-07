import asyncio
import pytest
from core.state import AppState

@pytest.mark.asyncio
async def test_app_state_lock():
    state = AppState()
    assert hasattr(state, 'lock')
    assert isinstance(state.lock, asyncio.Lock)
    
    # Test that we can acquire the lock
    async with state.lock:
        state.is_online = False
        
    assert state.is_online is False
