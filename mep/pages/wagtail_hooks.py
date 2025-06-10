from django.utils.html import format_html

import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail.admin.rich_text.converters.html_to_contentstate import BlockElementHandler
from wagtail import hooks
from webpack_loader.templatetags.webpack_loader import render_bundle

# blockquote registration example taken from:
# http://docs.wagtail.io/en/v2.4/advanced_topics/customisation/extending_draftail.html#creating-new-blocks


@hooks.register("register_rich_text_features")
def register_blockquote_feature(features):
    """
    Registering the `blockquote` feature, which uses the `blockquote` Draft.js block type,
    and is stored as HTML with a `<blockquote>` tag.
    """
    feature_name = "blockquote"
    type_ = "blockquote"
    tag = "blockquote"

    control = {
        "type": type_,
        "label": "❝",
        "description": "Blockquote",
        # Optionally, we can tell Draftail what element to use when displaying those blocks in the editor.
        "element": "blockquote",
    }

    features.register_editor_plugin(
        "draftail", feature_name, draftail_features.BlockFeature(control)
    )

    features.register_converter_rule(
        "contentstate",
        feature_name,
        {
            "from_database_format": {tag: BlockElementHandler(type_)},
            "to_database_format": {"block_map": {type_: tag}},
        },
    )

@hooks.register("insert_editor_js")
def editor_js():
    """Wagtail hook to include a JS bundle in the page editor, in html script
    tags. From PPA-django."""
    return format_html(render_bundle({}, "pdf", "js"))
