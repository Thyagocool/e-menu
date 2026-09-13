from httpx import AsyncClient


async def test_health_responds(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()