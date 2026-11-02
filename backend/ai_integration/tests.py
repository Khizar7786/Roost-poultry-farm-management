from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from .inference import roboflow_chick_counter


class RoboflowConfigurationTests(SimpleTestCase):
    def test_missing_key_is_reported_without_an_external_request(self):
        for value in ["", "   "]:
            with self.subTest(value=value), override_settings(ROBOFLOW_API_KEY=value):
                with patch.object(roboflow_chick_counter.requests, "post") as post:
                    with self.assertRaisesRegex(roboflow_chick_counter.RoboflowError, "ROBOFLOW_API_KEY"):
                        roboflow_chick_counter.count_from_image_bytes(b"test image")
                    post.assert_not_called()

    @override_settings(ROBOFLOW_API_KEY="example-test-key")
    def test_configured_key_is_used_for_the_request(self):
        response = Mock(status_code=200)
        response.json.return_value = {"outputs": [{"count": 0, "predictions": []}]}
        with patch.object(roboflow_chick_counter.requests, "post", return_value=response) as post:
            result = roboflow_chick_counter.count_from_image_bytes(b"test image")
        self.assertTrue(post.call_args.kwargs["json"]["api_key"] == "example-test-key")
        self.assertEqual(result["count"], 0)
