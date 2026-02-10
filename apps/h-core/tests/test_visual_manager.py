import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.visual.manager import AssetManager


@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_db():
    db = MagicMock()
    db._call = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_save_asset(temp_storage, mock_db):
    manager = AssetManager(mock_db, storage_path=temp_storage)

    # Create a dummy source file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"fake image data")
        source_path = tmp.name

    metadata = {
        "prompt": "a beautiful sunset",
        "embedding": [0.1] * 768,
        "agent_id": "electra",
        "tags": ["nature", "sunset"],
    }

    asset_url = await manager.save_asset(source_path, metadata)

    assert asset_url.startswith("file://")
    saved_path = asset_url.replace("file://", "")
    assert os.path.exists(saved_path)
    assert not os.path.exists(source_path)  # Should have been moved

    # Verify DB call
    mock_db._call.assert_called()
    # Find the call to 'create' 'visual_asset'
    create_call = next(c for c in mock_db._call.mock_calls if c.args[0] == "create" and c.args[1] == "visual_asset")
    data = create_call.args[2]
    assert data["prompt"] == "a beautiful sunset"
    assert data["agent_id"] == "electra"
    assert data["embedding"] == [0.1] * 768


@pytest.mark.asyncio
async def test_get_asset_by_prompt(temp_storage, mock_db):
    manager = AssetManager(mock_db, storage_path=temp_storage)

    mock_db._call.return_value = [{"result": [{"url": "file://fake", "score": 0.9}]}]

    results = await manager.get_asset_by_prompt(embedding=[0.1] * 768)

    assert len(results) == 1
    assert results[0]["url"] == "file://fake"
    mock_db._call.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_assets(temp_storage, mock_db):
    manager = AssetManager(mock_db, storage_path=temp_storage)

    # Create some files
    for i in range(5):
        path = os.path.join(temp_storage, f"img_{i}.jpg")
        with open(path, "wb") as f:
            f.write(b"x" * 1000)  # 1KB each
        # Set different access times (atime, mtime)
        # We use i as timestamp to ensure order
        os.utime(path, (1000 + i, 1000 + i))

    # Total size = 5000 bytes. Set quota to 2500 bytes.
    # Should delete files until <= 2500.
    # img_0, img_1, img_2 are the oldest.
    # After deleting img_0 (1000), total = 4000.
    # After deleting img_1 (1000), total = 3000.
    # After deleting img_2 (1000), total = 2000.
    # 2000 <= 2500, so it stops.

    await manager.cleanup_assets(quota_bytes=2500)

    remaining_files = os.listdir(temp_storage)
    assert len(remaining_files) == 2
    assert "img_3.jpg" in remaining_files
    assert "img_4.jpg" in remaining_files
    assert "img_0.jpg" not in remaining_files
    assert "img_1.jpg" not in remaining_files
    assert "img_2.jpg" not in remaining_files

    # Verify DB delete calls were made for deleted files
    assert mock_db._call.call_count >= 3
