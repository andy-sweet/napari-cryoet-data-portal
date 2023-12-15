from typing import TYPE_CHECKING, Optional

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QListWidgetItem,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from napari_cryoet_data_portal._listing_widget import ListingWidget
from napari_cryoet_data_portal._logging import logger
from napari_cryoet_data_portal._open_widget import OpenWidget
from napari_cryoet_data_portal._preview_widget import PreviewWidget
from napari_cryoet_data_portal._uri_widget import UriWidget

if TYPE_CHECKING:
    from napari.components import ViewerModel


class DataPortalWidget(QWidget):
    """The main widget for browsing the data portal from napari.

    This consists of a few privately defined sub-widgets, each of which
    has its own task with respect to the data portal like the initial
    connection or showing previews of a dataset or tomogram.
    Each task is run asynchronously and can be cancelled.

    Examples
    --------
    >>> from napari import Viewer
    >>> viewer = Viewer()
    >>> widget = DataPortalWidget(viewer)
    >>> viewer.window.add_dock_widget(widget)
    """

    def __init__(
        self, napari_viewer: "ViewerModel", parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        self._uri = UriWidget()

        self._listing = ListingWidget()
        self._listing.hide()

        self._preview = PreviewWidget()
        self._preview.hide()

        self._open = OpenWidget(napari_viewer)
        self._open.hide()

        self._uri.connected.connect(self._onUriConnected)
        self._uri.disconnected.connect(self._onUriDisconnected)
        self._listing.tree.currentItemChanged.connect(
            self._onListingItemChanged
        )
        self._preview.list.currentItemChanged.connect(
            self._onPreviewItemChanged
        )

        layout = QVBoxLayout()
        layout.addWidget(self._uri)
        layout.addWidget(self._listing, 1)
        layout.addWidget(self._preview, 1)
        layout.addWidget(self._open)
        layout.addStretch(0)

        self.setLayout(layout)

    def _onUriConnected(self, uri: str, filter: object) -> None:
        logger.debug("DataPortalWidget._onUriConnected")
        self._preview.setUri(uri)
        self._open.setUri(uri)
        self._listing.load(uri, filter=filter)

    def _onUriDisconnected(self) -> None:
        logger.debug("DataPortalWidget._onUriDisconnected")
        for widget in (self._listing, self._preview, self._open):
            widget.cancel()
            widget.hide()

    def _onListingItemChanged(
        self, item: QTreeWidgetItem, old_item: QTreeWidgetItem
    ) -> None:
        logger.debug("DataPortalWidget._onListingItemClicked: %s", item)
        self._open.hide()
        # The new current item can be none when reconnecting since that
        # clears the listing tree.
        if item is None:
            self._preview.hide()
        else:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            self._preview.load(data)

    def _onPreviewItemChanged(
        self, item: QListWidgetItem, old_item: QListWidgetItem 
    ) -> None:
        logger.debug("DataPortalWidget._onPreviewItemChanged: %s", item)
        # The new current item can be none when reconnecting since that
        # clears the preview list.
        if item is None:
            self._open.hide()
        else:
            data = item.data(Qt.ItemDataRole.UserRole)
            self._open.setTomogram(data)
