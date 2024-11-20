from typing import List, cast

import numpy as np
from cryoet_data_portal import AnnotationFile, Client, Tomogram, TomogramVoxelSpacing
from npe2.types import FullLayerData

from napari_cryoet_data_portal import read_tomogram
from napari_cryoet_data_portal._reader import read_annotation_file


def tomogram_10000_ts_026() -> List[FullLayerData]:
    """Returns tomogram TS_026 from dataset 10000 with annotations."""
    return _read_tomogram_from_10000("TS_026")


def tomogram_10000_ts_027() -> List[FullLayerData]:
    """Returns tomogram TS_027 from dataset 10000 with annotations."""
    return _read_tomogram_from_10000("TS_027")


def _read_tomogram_from_10000(name: str) -> List[FullLayerData]:
    client = Client()

    tomogram_spacing_url = f"https://files.cryoetdataportal.cziscience.com/10000/{name}/Reconstructions/VoxelSpacing13.480/"
    tomogram_spacing = cast(
        TomogramVoxelSpacing,
        TomogramVoxelSpacing.find(client, [
            TomogramVoxelSpacing.https_prefix == tomogram_spacing_url]
        ).pop()
    )

    tomogram: Tomogram = tomogram_spacing.tomograms.pop()

    tomogram_image = read_tomogram(tomogram)
    # Materialize lowest resolution for speed.
    tomogram_image = (np.asarray(tomogram_image[0][-1]), *tomogram_image[1:])
    tomogram_image[1]["scale"] = (4, 4, 4)

    anno_files = cast(
        List[AnnotationFile],
        AnnotationFile.find(client, [
            AnnotationFile.tomogram_voxel_spacing_id == tomogram_spacing.id
        ])
    )

    ribosome_anno_file = [
        f
        for f in anno_files
        if "cytosolic ribosome" in f.annotation_shape.annotation.object_name.lower()
    ].pop()
    fas_anno_file = [
        f
        for f in anno_files
        if "fatty acid synthase" in f.annotation_shape.annotation.object_name.lower()
    ].pop()
    ribosome_points = read_annotation_file(ribosome_anno_file, tomogram=tomogram)
    fatty_acid_points = read_annotation_file(fas_anno_file, tomogram=tomogram)

    return [
        tomogram_image,
        ribosome_points,
        fatty_acid_points,
    ]
