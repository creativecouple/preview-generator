# -*- coding: utf-8 -*-
import tempfile
import typing
import zipfile

from preview_generator.preview.builder.image__wand import ImagePreviewBuilderWand  # nopep8
from preview_generator.preview.generic_preview import PreviewBuilder
from preview_generator.utils import ImgDims
from preview_generator.utils import MimetypeMapping


class ImagePreviewBuilderSketch(PreviewBuilder):
    SKETCHUP_MIMETYPES_MAPPING = [MimetypeMapping("application/sketchup-backup", ".skb"),
                                  MimetypeMapping("application/sketchup-project", ".skp")                                  ]
    weight = 130

    @classmethod
    def get_label(cls) -> str:
        return "Images generator from sketchup files"

    @classmethod
    def get_supported_mimetypes(cls) -> typing.List[str]:
        mimetypes = []
        for mimetype_mapping in cls.get_mimetypes_mapping():
            mimetypes.append(mimetype_mapping.mimetype)
        return mimetypes

    @classmethod
    def get_mimetypes_mapping(cls) -> typing.List[MimetypeMapping]:
        return cls.SKETCHUP_MIMETYPES_MAPPING

    def build_jpeg_preview(
        self,
        file_path: str,
        preview_name: str,
        cache_path: str,
        page_id: int,
        extension: str = ".jpg",
        size: ImgDims = None,
        mimetype: str = "",
    ) -> None:
        if not size:
            size = self.default_size

        with open(file_path, "rb") as filestream:
            data = filestream.read()

            png_start = b"\x89PNG\r\n\x1a\n"
            png_end = b"IEND\xaeB`\x82"

            start = data.find(png_start)
            if start == -1:
                return

            end = data.find(png_end, start)
            if end == -1:
                return

            end += len(png_end)

        with tempfile.NamedTemporaryFile(prefix="preview-generator-", suffix='.png') as tmp_file:
            tmp_file.write(data[start:end])

            ImagePreviewBuilderWand().build_jpeg_preview(
                tmp_file.name,
                preview_name,
                cache_path,
                page_id,
                extension,
                size,
                mimetype,
            )

    def has_jpeg_preview(self) -> bool:
        return True

    def get_page_number(
        self, file_path: str, preview_name: str, cache_path: str, mimetype: str = ""
    ) -> int:
        return 1
