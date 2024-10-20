import pytest
from unittest.mock import patch
from scraper import getId, mp4, url_search, get_opts, get_video_info

video_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
long_video_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"


class TestBotFunctions:

    def test_url_search_valid_url(self):
        """Test url_search with a valid URL."""
        message = f"Check this out {video_url}"
        result = url_search(message)
        assert result == video_url

    def test_url_search_invalid_url(self):
        """Test url_search with no URL."""
        message = "There is no URL in this message"
        result = url_search(message)
        assert result == ""

    def test_get_short_video_info(self):
        """Test get_video_info using real URL of a short video"""
        result = get_video_info(video_url, get_opts(video_url, 'video'))
        assert result < 50

    def test_get_long_video_info(self):
        """Test get_video_info using real URL of a long video"""
        result = get_video_info(
            long_video_url, get_opts(long_video_url, 'video'))
        assert result > 50

    @pytest.mark.asyncio
    @patch('scraper.authorized_ids', [123456])
    async def test_get_user_id(self):
        """Test id command returning user's ID"""
        class MockMessage:
            text = ""

            async def reply_text(self, text):
                assert "Your ID is: 123456" in text

        class MockUser:
            id = 123456

        class MockUpdate:
            message = MockMessage()
            effective_user = MockUser()

        class MockContext:
            bot = None
        mock_update = MockUpdate()
        mock_context = MockContext()
        await getId(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_get_user_id_unauthorized_access(self):
        """Test id command rejecting unauthorized access"""
        class MockMessage:
            text = ""

            async def reply_text(self, text):
                assert "You are not authorized to use this bot." in text

        class MockUser:
            id = 123456

        class MockUpdate:
            message = MockMessage()
            effective_user = MockUser()

        class MockContext:
            bot = None
        mock_update = MockUpdate()
        mock_context = MockContext()
        await getId(mock_update, mock_context)

    @pytest.mark.asyncio
    @patch('scraper.authorized_ids', [123456])
    async def test_mp4_download_too_large(self):
        """Test mp4 command rejecting large files using a real URL."""
        class MockMessage:
            text = long_video_url

            async def reply_text(self, text):
                assert "is too big and cannot be sent using Telegram" in text

        class MockUser:
            id = 123456

        class MockUpdate:
            message = MockMessage()
            effective_user = MockUser()

        class MockContext:
            bot = None
        mock_update = MockUpdate()
        mock_context = MockContext()
        await mp4(mock_update, mock_context)

    @pytest.mark.asyncio
    @patch('scraper.authorized_ids', [123456])
    async def test_mp4_download(self):
        """Test mp4 command using a real URL."""
        class MockMessage:
            text = video_url

        class MockUser:
            id = 123456

        class MockUpdate:
            message = MockMessage()
            effective_user = MockUser()

        class MockBot:
            async def send_video(self, chat_id, video):
                assert chat_id == 123456
                assert video is not None

        class MockContext:
            bot = MockBot()

        mock_update = MockUpdate()
        mock_context = MockContext()
        await mp4(mock_update, mock_context)


if __name__ == '__main__':
    pytest.main()
