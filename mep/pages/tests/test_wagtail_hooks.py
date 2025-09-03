from unittest.mock import patch
from mep.pages.wagtail_hooks import editor_js


class TestWagtailHooks:
    # from ppa-django
    @patch("mep.pages.wagtail_hooks.render_bundle")
    def test_editor_js(self, mock_render_bundle):
        # should call render_bundle
        mock_script_tag = "<script src='pdf.js'></script>"
        mock_render_bundle.return_value = mock_script_tag
        inserted_js = editor_js()
        mock_render_bundle.assert_called_once_with({}, "pdf", "js")
        assert str(inserted_js) == mock_script_tag
