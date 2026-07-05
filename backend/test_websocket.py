import asyncio
import websockets
import json
import sys

async def test_websocket():
    uri = 'ws://localhost:8000/ws/testuser'
    try:
        async with websockets.connect(uri) as ws:
            # 发送消息
            await ws.send('hello')
            print('Sent: hello')

            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            print(f'Recv: type={data["type"]}, data={data["data"]}')
            
            # 断言
            assert data['type'] == 'echo', f'期望 type=echo，实际 {data["type"]}'
            assert data['data'] == 'hello', f'期望 data=hello，实际 {data["data"]}'
            print('[PASS] WebSocket test OK!')

    except websockets.exceptions.ConnectionClosedError as e:
        print(f'[FAIL] Connection closed: {e}')
        sys.exit(1)
    except websockets.exceptions.WebSocketException as e:
        print(f'[FAIL] WebSocket error: {e}')
        sys.exit(1)
    except asyncio.TimeoutError:
        print('[FAIL] Timeout - is server running?')
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f'[FAIL] JSON parse error: {e}')
        sys.exit(1)
    except AssertionError as e:
        print(f'[FAIL] Assertion: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'[FAIL] Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(test_websocket())