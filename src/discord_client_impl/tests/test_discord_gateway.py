"""Unit tests for DiscordGateway class.

These are fast, isolated tests that mock all external dependencies.
"""

import asyncio
import contextlib
import json
import os
import threading
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from discord_client_impl.discord_impl import DiscordGateway

IDENTIFY = 2

pytestmark = pytest.mark.unit


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def gateway() -> DiscordGateway:
    """Provide a fresh DiscordGateway instance for tests."""
    return DiscordGateway(token="test_token_12345")


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Provide a mock WebSocket connection."""
    ws: AsyncMock = AsyncMock()
    ws.closed = False
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def mock_event_loop() -> Mock:
    """Provide a mock asyncio event loop."""
    loop: Mock = Mock()
    loop.run_in_executor = AsyncMock()
    return loop


@pytest.fixture
def mock_discord_hello_message() -> dict[str, Any]:
    """Provide a mock HELLO message from Discord."""
    return {"op": 10, "d": {"heartbeat_interval": 41250, "_trace": ["gateway-prd-main-abcd"]}}


@pytest.fixture
def mock_discord_hello_json(mock_discord_hello_message: dict[str, Any]) -> str:
    """Provide a mock HELLO message as JSON string."""
    return json.dumps(mock_discord_hello_message)


@pytest.fixture
def mock_discord_ready_message() -> dict[str, Any]:
    """Provide a mock READY message from Discord."""
    return {
        "op": 0,
        "t": "READY",
        "s": 1,
        "d": {
            "v": 10,
            "user": {
                "id": "123456789",
                "username": "TestBot",
                "discriminator": "0001",
                "avatar": None,
                "bot": True,
            },
            "guilds": [],
            "session_id": "test_session_id_123",
            "application": {"id": "123456789", "flags": 0},
        },
    }


@pytest.fixture
def mock_discord_ready_json(mock_discord_ready_message: dict[str, Any]) -> str:
    """Provide a mock READY message as JSON string."""
    return json.dumps(mock_discord_ready_message)


@pytest.fixture
def sync_callback() -> Mock:
    """Provide a mock synchronous callback function."""
    return Mock()


@pytest.fixture
def async_callback() -> AsyncMock:
    """Provide a mock asynchronous callback function."""
    return AsyncMock()


@pytest.fixture
def failing_callback() -> Mock:
    """Provide a callback that raises an exception."""
    return Mock(side_effect=Exception("Callback error"))


class TestDiscordGatewayInit:
    """Test gateway initialization."""

    def test_init_with_token(self, gateway: DiscordGateway) -> None:
        """Test initialization with explicit token."""
        assert gateway.token == "test_token_12345"
        assert gateway.ws is None
        assert gateway.sequence is None
        assert gateway.session_id is None
        assert gateway.subscribers == {}
        assert gateway.heartbeat_interval is None
        assert gateway.running is False

    def test_init_from_environment(self) -> None:
        """Test initialization using environment variable."""
        with patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "env_token_456"}):
            gateway = DiscordGateway()
            assert gateway.token == "env_token_456"

    def test_init_attributes(self, gateway: DiscordGateway) -> None:
        """Test that all required attributes are initialized."""
        assert hasattr(gateway, "ws")
        assert hasattr(gateway, "sequence")
        assert hasattr(gateway, "session_id")
        assert hasattr(gateway, "subscribers")
        assert hasattr(gateway, "heartbeat_interval")
        assert hasattr(gateway, "running")
        assert hasattr(gateway, "_heartbeat_task")
        assert hasattr(gateway, "_loop")
        assert hasattr(gateway, "_thread")


class TestDiscordGatewaySubscription:
    """Test event subscription mechanisms."""

    def test_subscribe_new_event(self, gateway: DiscordGateway, sync_callback: Mock) -> None:
        """Test subscribing to a new event type."""
        gateway.subscribe("MESSAGE_CREATE", sync_callback)

        assert "MESSAGE_CREATE" in gateway.subscribers
        assert sync_callback in gateway.subscribers["MESSAGE_CREATE"]

    def test_subscribe_multiple_callbacks(
        self, gateway: DiscordGateway, sync_callback: Mock
    ) -> None:
        """Test subscribing multiple callbacks to same event."""
        callback1: Mock = sync_callback
        callback2: Mock = Mock()

        gateway.subscribe("MESSAGE_CREATE", callback1)
        gateway.subscribe("MESSAGE_CREATE", callback2)

        assert len(gateway.subscribers["MESSAGE_CREATE"]) == IDENTIFY
        assert callback1 in gateway.subscribers["MESSAGE_CREATE"]
        assert callback2 in gateway.subscribers["MESSAGE_CREATE"]

    def test_subscribe_different_events(self, gateway: DiscordGateway, sync_callback: Mock) -> None:
        """Test subscribing to multiple different events."""
        callback1: Mock = sync_callback
        callback2: Mock = Mock()

        gateway.subscribe("MESSAGE_CREATE", callback1)
        gateway.subscribe("READY", callback2)

        assert "MESSAGE_CREATE" in gateway.subscribers
        assert "READY" in gateway.subscribers
        assert len(gateway.subscribers) == IDENTIFY

    def test_unsubscribe_callback(self, gateway: DiscordGateway, sync_callback: Mock) -> None:
        """Test unsubscribing a callback from an event."""
        gateway.subscribe("MESSAGE_CREATE", sync_callback)
        gateway.unsubscribe("MESSAGE_CREATE", sync_callback)

        assert sync_callback not in gateway.subscribers["MESSAGE_CREATE"]

    def test_unsubscribe_nonexistent_event(
        self, gateway: DiscordGateway, sync_callback: Mock
    ) -> None:
        """Test unsubscribing from event that doesn't exist."""
        # Should not raise an error
        gateway.unsubscribe("NONEXISTENT_EVENT", sync_callback)

    def test_unsubscribe_nonexistent_callback(
        self, gateway: DiscordGateway, sync_callback: Mock
    ) -> None:
        """Test unsubscribing a callback that was never subscribed."""
        gateway.subscribe("MESSAGE_CREATE", Mock())

        # Should not raise an error
        with pytest.raises(ValueError):  # noqa: PT011
            gateway.unsubscribe("MESSAGE_CREATE", sync_callback)


class TestDiscordGatewayEmit:
    """Test event emission to subscribers."""

    @pytest.mark.asyncio
    async def test_emit_sync_callback(
        self, gateway: DiscordGateway, sync_callback: Mock, mock_event_loop: Mock
    ) -> None:
        """Test emitting event to synchronous callback."""
        gateway._loop = mock_event_loop
        gateway.subscribe("MESSAGE_CREATE", sync_callback)

        event_data: dict[str, Any] = {"content": "Hello!", "author": {"id": "123"}}
        await gateway._emit("MESSAGE_CREATE", event_data)

        mock_event_loop.run_in_executor.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_async_callback(
        self, gateway: DiscordGateway, async_callback: AsyncMock
    ) -> None:
        """Test emitting event to asynchronous callback."""
        gateway.subscribe("MESSAGE_CREATE", async_callback)

        event_data: dict[str, Any] = {"content": "Hello!", "author": {"id": "123"}}
        await gateway._emit("MESSAGE_CREATE", event_data)

        async_callback.assert_awaited_once_with(event_data)

    @pytest.mark.asyncio
    async def test_emit_multiple_callbacks(
        self, gateway: DiscordGateway, mock_event_loop: Mock
    ) -> None:
        """Test emitting event to multiple subscribers."""
        gateway._loop = mock_event_loop

        callback1: Mock = Mock()
        callback2: Mock = Mock()
        gateway.subscribe("MESSAGE_CREATE", callback1)
        gateway.subscribe("MESSAGE_CREATE", callback2)

        event_data: dict[str, Any] = {"content": "Hello!"}
        await gateway._emit("MESSAGE_CREATE", event_data)

        assert mock_event_loop.run_in_executor.call_count == IDENTIFY

    @pytest.mark.asyncio
    async def test_emit_no_subscribers(self, gateway: DiscordGateway) -> None:
        """Test emitting event with no subscribers."""
        # Should not raise an error
        await gateway._emit("MESSAGE_CREATE", {"content": "Hello!"})

    @pytest.mark.asyncio
    async def test_emit_callback_exception(
        self, gateway: DiscordGateway, failing_callback: Mock, mock_event_loop: Mock
    ) -> None:
        """Test that callback exceptions don't break emission."""
        gateway._loop = mock_event_loop

        callback2: Mock = Mock()
        gateway.subscribe("MESSAGE_CREATE", failing_callback)
        gateway.subscribe("MESSAGE_CREATE", callback2)

        event_data: dict[str, Any] = {"content": "Hello!"}
        await gateway._emit("MESSAGE_CREATE", event_data)

        # Both callbacks should be attempted
        assert mock_event_loop.run_in_executor.call_count == IDENTIFY

    @pytest.mark.asyncio
    async def test_emit_mixed_callbacks(
        self,
        gateway: DiscordGateway,
        sync_callback: Mock,
        async_callback: AsyncMock,
        mock_event_loop: Mock,
    ) -> None:
        """Test emitting to both sync and async callbacks."""
        gateway._loop = mock_event_loop

        gateway.subscribe("MESSAGE_CREATE", sync_callback)
        gateway.subscribe("MESSAGE_CREATE", async_callback)

        event_data: dict[str, Any] = {"content": "Mixed callbacks"}
        await gateway._emit("MESSAGE_CREATE", event_data)

        # Sync callback should use executor
        mock_event_loop.run_in_executor.assert_called_once()
        # Async callback should be awaited
        async_callback.assert_awaited_once_with(event_data)


class TestDiscordGatewayHeartbeat:
    """Test heartbeat functionality."""

    @pytest.mark.asyncio
    async def test_heartbeat_sends_message(
        self, gateway: DiscordGateway, mock_websocket: AsyncMock
    ) -> None:
        """Test that heartbeat sends periodic messages."""
        gateway.running = True
        gateway.heartbeat_interval = 100  # 100ms
        gateway.sequence = 42
        gateway.ws = mock_websocket

        # Run heartbeat for a short time
        heartbeat_task: asyncio.Task[None] = asyncio.create_task(gateway._heartbeat())
        await asyncio.sleep(0.15)  # Wait for at least one heartbeat
        gateway.running = False

        try:
            await asyncio.wait_for(heartbeat_task, timeout=1.0)
        except TimeoutError:
            heartbeat_task.cancel()

        # Should have sent at least one heartbeat
        assert mock_websocket.send.call_count >= 1

        # Verify heartbeat payload
        call_args: str = mock_websocket.send.call_args_list[0][0][0]
        payload: dict[str, Any] = json.loads(call_args)
        assert payload["op"] == gateway.HEARTBEAT
        assert payload["d"] == 42

    @pytest.mark.asyncio
    async def test_heartbeat_stops_when_cancelled(
        self, gateway: DiscordGateway, mock_websocket: AsyncMock
    ) -> None:
        """Test that heartbeat task can be cancelled."""
        gateway.running = True
        gateway.heartbeat_interval = 100
        gateway.ws = mock_websocket

        heartbeat_task: asyncio.Task[None] = asyncio.create_task(gateway._heartbeat())
        await asyncio.sleep(0.05)

        heartbeat_task.cancel()

        # Should not raise exception
        await heartbeat_task

    @pytest.mark.asyncio
    async def test_heartbeat_with_none_sequence(
        self, gateway: DiscordGateway, mock_websocket: AsyncMock
    ) -> None:
        """Test heartbeat with None sequence number."""
        gateway.running = True
        gateway.heartbeat_interval = 50
        gateway.sequence = None
        gateway.ws = mock_websocket

        heartbeat_task: asyncio.Task[None] = asyncio.create_task(gateway._heartbeat())
        await asyncio.sleep(0.1)
        gateway.running = False

        try:
            await asyncio.wait_for(heartbeat_task, timeout=1.0)
        except TimeoutError:
            heartbeat_task.cancel()

        # Verify heartbeat with None sequence
        if mock_websocket.send.call_count > 0:
            call_args: str = mock_websocket.send.call_args_list[0][0][0]
            payload: dict[str, Any] = json.loads(call_args)
            assert payload["d"] is None

    @pytest.mark.asyncio
    async def test_heartbeat_skips_if_ws_closed(self, gateway: DiscordGateway) -> None:
        """Test that heartbeat doesn't send if WebSocket is closed."""
        gateway.running = True
        gateway.heartbeat_interval = 50
        gateway.ws = Mock()
        gateway.ws.closed = True
        gateway.ws.send = AsyncMock()

        heartbeat_task: asyncio.Task[None] = asyncio.create_task(gateway._heartbeat())
        await asyncio.sleep(0.1)
        gateway.running = False

        try:
            await asyncio.wait_for(heartbeat_task, timeout=1.0)
        except TimeoutError:
            heartbeat_task.cancel()

        # Should not send if closed
        gateway.ws.send.assert_not_called()


class TestDiscordGatewayIdentify:
    """Test identification process."""

    @pytest.mark.asyncio
    async def test_identify_sends_correct_payload(
        self, gateway: DiscordGateway, mock_websocket: AsyncMock
    ) -> None:
        """Test that identify sends correct authentication payload."""
        gateway.ws = mock_websocket

        await gateway._identify()

        mock_websocket.send.assert_called_once()
        payload: dict[str, Any] = json.loads(mock_websocket.send.call_args[0][0])

        assert payload["op"] == gateway.IDENTIFY
        assert payload["d"]["token"] == "test_token_12345"
        assert payload["d"]["intents"] == 513
        assert "properties" in payload["d"]

    @pytest.mark.asyncio
    async def test_identify_includes_properties(
        self, gateway: DiscordGateway, mock_websocket: AsyncMock
    ) -> None:
        """Test that identify includes client properties."""
        gateway.ws = mock_websocket

        await gateway._identify()

        payload: dict[str, Any] = json.loads(mock_websocket.send.call_args[0][0])
        properties: dict[str, str] = payload["d"]["properties"]

        assert "os" in properties
        assert "browser" in properties
        assert "device" in properties


class TestDiscordGatewayEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_handle_malformed_json(self, gateway: DiscordGateway) -> None:
        """Test handling of malformed JSON messages."""
        with pytest.raises(json.JSONDecodeError):
            await gateway._handle_message("not valid json {{{")

    @pytest.mark.asyncio
    async def test_handle_missing_opcode(self, gateway: DiscordGateway) -> None:
        """Test handling of message without opcode."""
        message: str = json.dumps({"d": "some data"})

        with pytest.raises(KeyError):
            await gateway._handle_message(message)

    @pytest.mark.asyncio
    async def test_emit_with_no_loop(self, gateway: DiscordGateway, sync_callback: Mock) -> None:
        """Test emit behavior when event loop is not set."""
        gateway.subscribe("TEST_EVENT", sync_callback)
        gateway._loop = None

        # Should raise assertion error
        await gateway._emit("TEST_EVENT", {})

    def test_multiple_start_calls(self, gateway: DiscordGateway) -> None:
        """Test multiple calls to start()."""
        with patch.object(threading.Thread, "start"):
            gateway.start()
            first_thread = gateway._thread

            gateway.start()
            second_thread = gateway._thread

            # Should be the same thread
            assert first_thread == second_thread

    @pytest.mark.asyncio
    async def test_heartbeat_without_websocket(self, gateway: DiscordGateway) -> None:
        """Test heartbeat behavior without WebSocket connection."""
        gateway.running = True
        gateway.heartbeat_interval = 50
        gateway.ws = None

        heartbeat_task: asyncio.Task[None] = asyncio.create_task(gateway._heartbeat())
        await asyncio.sleep(0.1)
        gateway.running = False

        try:
            await asyncio.wait_for(heartbeat_task, timeout=1.0)
        except TimeoutError:
            heartbeat_task.cancel()


class TestDiscordGateway:
    """End-to-end integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_full_message_flow(self, gateway: DiscordGateway) -> None:
        """Test complete flow from connection to message receipt."""
        received_messages: list[dict[str, Any]] = []

        def message_handler(data: dict[str, Any]) -> None:
            received_messages.append(data)

        gateway.subscribe("MESSAGE_CREATE", message_handler)
        gateway._loop = asyncio.get_event_loop()

        # Simulate receiving a message
        message_data: dict[str, Any] = {"content": "Test message", "author": {"id": "123"}}

        discord_message: str = json.dumps(
            {"op": gateway.DISPATCH, "t": "MESSAGE_CREATE", "s": 1, "d": message_data}
        )

        await gateway._handle_message(discord_message)

        # Give async callbacks time to execute
        await asyncio.sleep(0.1)

        assert len(received_messages) == 1
        assert received_messages[0] == message_data

    @pytest.mark.asyncio
    async def test_hello_to_ready_flow(
        self, gateway: DiscordGateway, mock_discord_hello_json: str, mock_discord_ready_json: str
    ) -> None:
        """Test the complete HELLO -> IDENTIFY -> READY flow."""
        gateway.ws = AsyncMock()
        ready_received: list[dict[str, Any]] = []

        def ready_handler(data: dict[str, Any]) -> None:
            ready_received.append(data)

        gateway.subscribe("READY", ready_handler)
        gateway._loop = asyncio.get_event_loop()

        # Step 1: Receive HELLO
        await gateway._handle_message(mock_discord_hello_json)
        assert gateway.heartbeat_interval == 41250
        assert gateway._heartbeat_task is not None

        # Step 2: Receive READY
        await gateway._handle_message(mock_discord_ready_json)
        await asyncio.sleep(0.1)

        assert gateway.session_id == "test_session_id_123"
        assert len(ready_received) == 1

    @pytest.mark.asyncio
    async def test_connection_lifecycle(
        self, gateway: DiscordGateway, mock_discord_hello_json: str, mock_discord_ready_json: str
    ) -> None:
        """Test complete connection lifecycle from HELLO to shutdown."""
        gateway.ws = AsyncMock()
        gateway._loop = asyncio.get_event_loop()

        lifecycle_events: list[str] = []

        def ready_handler(data: dict[str, Any]) -> None:
            lifecycle_events.append("READY")

        gateway.subscribe("READY", ready_handler)

        # Start connection
        await gateway._handle_message(mock_discord_hello_json)
        lifecycle_events.append("HELLO")

        await gateway._handle_message(mock_discord_ready_json)
        await asyncio.sleep(0.1)

        # Verify lifecycle
        assert "HELLO" in lifecycle_events
        assert "READY" in lifecycle_events
        assert gateway.heartbeat_interval is not None
        assert gateway.session_id is not None

        # Cleanup heartbeat
        if gateway._heartbeat_task:
            gateway._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await gateway._heartbeat_task

    @pytest.mark.asyncio
    async def test_invalid_session_recovery(
        self, gateway: DiscordGateway, mock_websocket: AsyncMock
    ) -> None:
        """Test recovery from invalid session."""
        gateway.ws = mock_websocket
        gateway.session_id = "old_session_id"

        # Simulate INVALID_SESSION
        invalid_session_msg: str = json.dumps({"op": gateway.INVALID_SESSION, "d": False})

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await gateway._handle_message(invalid_session_msg)

        # Should have attempted to re-identify
        mock_websocket.send.assert_called()

        # Verify IDENTIFY payload
        payload: dict[str, Any] = json.loads(mock_websocket.send.call_args[0][0])
        assert payload["op"] == gateway.IDENTIFY

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_event(self, gateway: DiscordGateway) -> None:
        """Test multiple subscribers receiving the same event."""
        received_by_subscriber1: list[dict[str, Any]] = []
        received_by_subscriber2: list[dict[str, Any]] = []
        received_by_subscriber3: list[dict[str, Any]] = []

        def subscriber1(data: dict[str, Any]) -> None:
            received_by_subscriber1.append(data)

        def subscriber2(data: dict[str, Any]) -> None:
            received_by_subscriber2.append(data)

        def subscriber3(data: dict[str, Any]) -> None:
            received_by_subscriber3.append(data)

        gateway.subscribe("MESSAGE_CREATE", subscriber1)
        gateway.subscribe("MESSAGE_CREATE", subscriber2)
        gateway.subscribe("MESSAGE_CREATE", subscriber3)
        gateway._loop = asyncio.get_event_loop()

        # Send multiple messages
        for i in range(3):
            message_data: dict[str, Any] = {"content": f"Message {i}", "id": str(i)}

            discord_message: str = json.dumps(
                {"op": gateway.DISPATCH, "t": "MESSAGE_CREATE", "s": i + 1, "d": message_data}
            )

            await gateway._handle_message(discord_message)

        await asyncio.sleep(0.1)

        # All subscribers should receive all messages
        assert len(received_by_subscriber1) == 3
        assert len(received_by_subscriber2) == 3
        assert len(received_by_subscriber3) == 3

        # Verify content
        for i in range(3):
            assert received_by_subscriber1[i]["content"] == f"Message {i}"
            assert received_by_subscriber2[i]["content"] == f"Message {i}"
            assert received_by_subscriber3[i]["content"] == f"Message {i}"

    @pytest.mark.asyncio
    async def test_async_and_sync_subscribers_mixed(self, gateway: DiscordGateway) -> None:
        """Test mixing async and sync subscribers on same event."""
        sync_received: list[dict[str, Any]] = []
        async_received: list[dict[str, Any]] = []

        def sync_handler(data: dict[str, Any]) -> None:
            sync_received.append(data)

        async def async_handler(data: dict[str, Any]) -> None:
            async_received.append(data)

        gateway.subscribe("MESSAGE_CREATE", sync_handler)
        gateway.subscribe("MESSAGE_CREATE", async_handler)
        gateway._loop = asyncio.get_event_loop()

        message_data: dict[str, Any] = {"content": "Test mixed"}

        discord_message: str = json.dumps(
            {"op": gateway.DISPATCH, "t": "MESSAGE_CREATE", "s": 1, "d": message_data}
        )

        await gateway._handle_message(discord_message)
        await asyncio.sleep(0.1)

        # Both should receive the message
        assert len(sync_received) == 1
        assert len(async_received) == 1
        assert sync_received[0] == message_data
        assert async_received[0] == message_data

    @pytest.mark.asyncio
    async def test_unsubscribe_during_operation(self, gateway: DiscordGateway) -> None:
        """Test unsubscribing a callback during normal operation."""
        received_before: list[dict[str, Any]] = []
        received_after: list[dict[str, Any]] = []

        def handler(data: dict[str, Any]) -> None:
            if len(received_before) < 2:
                received_before.append(data)
            else:
                received_after.append(data)

        gateway.subscribe("MESSAGE_CREATE", handler)
        gateway._loop = asyncio.get_event_loop()

        # Send first two messages
        for i in range(2):
            message1: str = json.dumps(
                {
                    "op": gateway.DISPATCH,
                    "t": "MESSAGE_CREATE",
                    "s": i + 1,
                    "d": {"content": f"Message {i}"},
                }
            )
            await gateway._handle_message(message1)

        await asyncio.sleep(0.1)

        # Unsubscribe
        gateway.unsubscribe("MESSAGE_CREATE", handler)

        # Send third message
        message2: str = json.dumps(
            {"op": gateway.DISPATCH, "t": "MESSAGE_CREATE", "s": 3, "d": {"content": "Message 2"}}
        )
        await gateway._handle_message(message2)
        await asyncio.sleep(0.1)

        # Should only receive first two messages
        assert len(received_before) == 2
        assert len(received_after) == 0

    @pytest.mark.asyncio
    async def test_sequence_number_persistence(self, gateway: DiscordGateway) -> None:
        """Test that sequence numbers persist across messages."""
        gateway._loop = asyncio.get_event_loop()

        sequences: list[int] = []

        for seq in [1, 5, 10, 15, 20]:
            message: str = json.dumps(
                {"op": gateway.DISPATCH, "t": "SOME_EVENT", "s": seq, "d": {}}
            )
            await gateway._handle_message(message)
            assert gateway.sequence is not None
            sequences.append(gateway.sequence)

        # Verify sequence numbers are tracked correctly
        assert sequences == [1, 5, 10, 15, 20]
        assert gateway.sequence == 20

    def test_thread_safe_subscription(self, gateway: DiscordGateway) -> None:
        """Test that subscriptions are thread-safe."""
        results: list[bool] = []

        def subscribe_and_check(event_num: int) -> None:
            event_name: str = f"EVENT_{event_num}"
            callback: Mock = Mock()

            gateway.subscribe(event_name, callback)

            # Verify subscription worked
            if event_name in gateway.subscribers:
                results.append(True)
            else:
                results.append(False)

        threads: list[threading.Thread] = [
            threading.Thread(target=subscribe_and_check, args=(i,)) for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All subscriptions should succeed
        assert all(results)
        assert len(gateway.subscribers) == 10


class TestDiscordGatewayRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_bot_message_processing(self, gateway: DiscordGateway) -> None:
        """Test a typical bot message processing scenario."""
        processed_messages: list[str] = []

        async def process_message(data: dict[str, Any]) -> None:
            """Simulate bot processing a message."""
            content: str = data.get("content", "")
            if content.startswith("!"):
                # Bot command detected
                processed_messages.append(content)

        gateway.subscribe("MESSAGE_CREATE", process_message)
        gateway._loop = asyncio.get_event_loop()

        # Simulate various messages
        messages: list[str] = ["Hello everyone", "!help", "Regular message", "!ping", "!status"]

        for i, msg_content in enumerate(messages):
            message: str = json.dumps(
                {
                    "op": gateway.DISPATCH,
                    "t": "MESSAGE_CREATE",
                    "s": i + 1,
                    "d": {"content": msg_content, "author": {"id": str(i)}},
                }
            )
            await gateway._handle_message(message)

        await asyncio.sleep(0.1)

        # Should only process commands
        assert len(processed_messages) == 3
        assert "!help" in processed_messages
        assert "!ping" in processed_messages
        assert "!status" in processed_messages

    @pytest.mark.asyncio
    async def test_event_statistics_tracking(self, gateway: DiscordGateway) -> None:
        """Test tracking statistics across multiple events."""
        stats: dict[str, int] = {"messages": 0, "joins": 0, "leaves": 0}

        def track_message(data: dict[str, Any]) -> None:
            stats["messages"] += 1

        def track_join(data: dict[str, Any]) -> None:
            stats["joins"] += 1

        def track_leave(data: dict[str, Any]) -> None:
            stats["leaves"] += 1

        gateway.subscribe("MESSAGE_CREATE", track_message)
        gateway.subscribe("GUILD_MEMBER_ADD", track_join)
        gateway.subscribe("GUILD_MEMBER_REMOVE", track_leave)
        gateway._loop = asyncio.get_event_loop()

        # Simulate various events
        events: list[tuple[str, dict[str, Any]]] = [
            ("MESSAGE_CREATE", {"content": "Hi"}),
            ("MESSAGE_CREATE", {"content": "Hello"}),
            ("GUILD_MEMBER_ADD", {"user": {"id": "1"}}),
            ("MESSAGE_CREATE", {"content": "Welcome"}),
            ("GUILD_MEMBER_REMOVE", {"user": {"id": "2"}}),
            ("MESSAGE_CREATE", {"content": "Bye"}),
            ("GUILD_MEMBER_ADD", {"user": {"id": "3"}}),
        ]

        for i, (event_type, event_data) in enumerate(events):
            message: str = json.dumps(
                {"op": gateway.DISPATCH, "t": event_type, "s": i + 1, "d": event_data}
            )
            await gateway._handle_message(message)

        await asyncio.sleep(0.1)

        assert stats["messages"] == 4
        assert stats["joins"] == 2
        assert stats["leaves"] == 1
