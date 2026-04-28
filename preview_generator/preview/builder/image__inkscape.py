# -*- coding: utf-8 -*-
from shutil import which
from subprocess import CalledProcessError
from subprocess import DEVNULL
from subprocess import STDOUT
from subprocess import check_call
from subprocess import check_output
import tempfile
import typing

from preview_generator.exception import BuilderDependencyNotFound
from preview_generator.exception import IntermediateFileBuildingFailed
from preview_generator.preview.builder.image__wand import ImagePreviewBuilderWand  # nopep8
from preview_generator.preview.generic_preview import ImagePreviewBuilder
from preview_generator.utils import ImgDims
from preview_generator.utils import executable_is_available

INKSCAPE_EXECUTABLE = "inkscape"

INKSCAPE_SVG_TO_PNG_OPTIONS = ("--export-area-drawing", "--export-type=png", "-o")
INKSCAPE_SVG_TO_PDF_OPTIONS = ("--export-area-drawing", "--export-type=pdf", "-o")

try:
    inkscape_version = check_output((INKSCAPE_EXECUTABLE, "--version"))
except (FileNotFoundError, CalledProcessError):
    inkscape_version = b"not_installed"


def get_inkscape_query_parameters(input_path: str) -> typing.Tuple[str, ...]:
    return (INKSCAPE_EXECUTABLE, input_path, "--query-width", "--query-height")

def get_inkscape_convert_png_parameters(input_path: str, output_path: str, size_dimension: str, size: int) -> typing.Tuple[str, ...]:
    return (INKSCAPE_EXECUTABLE, input_path, "--export-area-drawing", "--export-type=png", f"--export-{size_dimension}={size}", "-o", output_path)

def get_inkscape_convert_pdf_parameters(input_path: str, output_path: str) -> typing.Tuple[str, ...]:
    return (INKSCAPE_EXECUTABLE, input_path, "--export-area-drawing", "--export-type=pdf", "-o", output_path)


class ImagePreviewBuilderInkscape(ImagePreviewBuilder):
    weight = 70

    @classmethod
    def get_label(cls) -> str:
        return "Vector images - based on Inkscape"

    @classmethod
    def get_supported_mimetypes(cls) -> typing.List[str]:
        return ["image/svg+xml", "image/svg"]

    @classmethod
    def check_dependencies(cls) -> None:
        if not executable_is_available(INKSCAPE_EXECUTABLE):
            raise BuilderDependencyNotFound("this builder requires inkscape to be available")

    @classmethod
    def dependencies_versions(cls) -> typing.Optional[str]:
        return "{} from {}".format(inkscape_version.decode(), which(INKSCAPE_EXECUTABLE))

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
        # inkscape tesselation-P3.svg  -e
        with tempfile.NamedTemporaryFile(
            "w+b", prefix="preview-generator-", suffix=".png"
        ) as tmp_png:
            width,height = check_output(get_inkscape_query_parameters(file_path), text=True).split('\n')[0:2]
            orientation_landscape = (float(width) * size.height) > (float(height) * size.width)

            build_png_result_code = check_call(
                get_inkscape_convert_png_parameters(file_path, tmp_png.name, 'width', size.width)
                if orientation_landscape
                else get_inkscape_convert_png_parameters(file_path, tmp_png.name, 'height', size.height),
                stdout=DEVNULL,
                stderr=STDOUT,
            )

            if build_png_result_code != 0:
                raise IntermediateFileBuildingFailed(
                    "Building PNG intermediate file using inkscape "
                    "failed with status {}".format(build_png_result_code)
                )

            return ImagePreviewBuilderWand().build_jpeg_preview(
                tmp_png.name, preview_name, cache_path, page_id, extension, size, mimetype
            )

    def build_pdf_preview(
        self,
        file_path: str,
        preview_name: str,
        cache_path: str,
        extension: str = ".pdf",
        page_id: int = -1,
        mimetype: str = "",
    ) -> None:
        """
        generate pdf preview
        """
        build_pdf_result_code = check_call(
            get_inkscape_convert_pdf_parameters(file_path, cache_path + preview_name + extension),
            stdout=DEVNULL,
            stderr=STDOUT,
        )

        if build_pdf_result_code != 0:
            raise IntermediateFileBuildingFailed(
                "Building PDF file using inkscape "
                "failed with status {}".format(build_pdf_result_code)
            )
