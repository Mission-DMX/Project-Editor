# coding=utf-8
"""Scene module"""
from typing import Optional, TYPE_CHECKING

from .filter import Filter

if TYPE_CHECKING:
    from .board_configuration import BoardConfiguration
    from .control_desk import BankSet
    from .ui_configuration import UIPage


class FilterPage:
    def __init__(self, parent: "Scene"):
        self._filters: list[Filter] = []
        self._child_pages: list["FilterPage"] = []
        self._parent_scene: "Scene" = parent
        self._name: str = ""

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = str(new_name)

    @property
    def filters(self) -> list[Filter]:
        return self._filters

    @property
    def child_pages(self) -> list["FilterPage"]:
        return self._child_pages

    @property
    def parent_scene(self) -> "Scene":
        return self._parent_scene

    def copy(self, new_scene: "Scene" = None):
        if not new_scene:
            new_fp = FilterPage(self._parent_scene)
            # Internal copying should not copy filters as they are unique within scene
        else:
            new_fp = FilterPage(new_scene)
            for filter in self._filters:
                found_filter = new_scene.get_filter_by_id(filter.filter_id)
                if found_filter:
                    new_fp._filters.append(found_filter)
        for child_fp in self._child_pages:
            new_fp._child_pages.append(child_fp.copy(new_scene))
        new_fp._name = self.name
        return new_fp


class Scene:
    """Scene for show file."""

    def __init__(self, scene_id: int,
                 human_readable_name: str,
                 board_configuration: "BoardConfiguration"):
        self._scene_id: int = scene_id
        self._human_readable_name: str = human_readable_name
        self._board_configuration: "BoardConfiguration" = board_configuration
        self._filters: list[Filter] = []
        self._filter_index: dict[str, Filter] = {}
        self._filter_pages: list[FilterPage] = []
        self._associated_bankset: Optional["BankSet"] | None = None
        self._ui_pages: list["UIPage"] = []

    @property
    def scene_id(self) -> int:
        """The unique id of the scene"""
        return self._scene_id

    @property
    def human_readable_name(self) -> str:
        """The human readable name of the scene displayed by the ui"""
        return self._human_readable_name

    @human_readable_name.setter
    def human_readable_name(self, human_readable_name: str):
        """Sets the human readable name of the scene displayed by the ui"""
        self._human_readable_name = human_readable_name

    @property
    def board_configuration(self) -> "BoardConfiguration":
        """The board configuration the scene is part of"""
        return self._board_configuration

    @property
    def filters(self) -> list[Filter]:
        """The filters of the scene"""
        return self._filters

    @property
    def pages(self) -> list[FilterPage]:
        """Returns the associated list of filter pages"""
        if len(self._filter_pages) == 0:
            default_page = FilterPage(self)
            default_page.name = "default"
            for f in self._filters:
                default_page.filters.append(f)
            self._filter_pages.append(default_page)
        return self._filter_pages

    def insert_filterpage(self, fp: FilterPage):
        self._filter_pages.append(fp)

    @property
    def linked_bankset(self) -> Optional["BankSet"] | None:
        return self._associated_bankset

    @linked_bankset.setter
    def linked_bankset(self, new_bs: "BankSet"):
        if self._associated_bankset:
            if self._associated_bankset.is_linked:
                self._associated_bankset.unlink()
        self._associated_bankset = new_bs

    @property
    def ui_pages(self) -> list["UIPage"]:
        return self._ui_pages

    def __str__(self) -> str:
        if self.human_readable_name:
            return self.human_readable_name
        return str(self._scene_id)

    def ensure_bankset(self) -> bool:
        if self._associated_bankset is None:
            from .control_desk import BankSet
            self._associated_bankset = BankSet(description="Bankset associated with scene {}.".format(self._scene_id),
                                               gui_controlled=True)
            return False
        return True

    def copy(self, existing_scenes: list["Scene"]) -> "Scene":
        """
        This method returns a copy of the scene, jet containing a new unique ID.

        existing_scenes: A list of scenes to check the new id against.
        """
        chosen_id = len(existing_scenes)
        id_check_passed: bool = False
        while not id_check_passed:
            for s in existing_scenes:
                if chosen_id == s.scene_id:
                    chosen_id *= 2
                    break
            id_check_passed = True
        scene = Scene(scene_id=chosen_id,
                      human_readable_name=str(self.human_readable_name),
                      board_configuration=self.board_configuration)
        for f in self._filters:
            new_filter = f.copy(new_scene=scene)
            scene.append_filter(new_filter)
        for fp in self._filter_pages:
            scene._filter_pages.append(fp.copy(scene))
        scene.linked_bankset = self._associated_bankset.copy()
        for page in self._ui_pages:
            scene._ui_pages.append(page.copy(scene))
        return scene

    def get_filter_by_id(self, fid: str) -> Filter | None:
        f = self._filter_index.get(fid)
        if f:
            return f
        for f in self._filters:
            if f.filter_id == fid:
                self._filter_index[fid] = f
                return f
        return None

    def append_filter(self, f: Filter):
        self._filters.append(f)
        self._filter_index[f.filter_id] = f

    def remove_filter(self, f: Filter):
        self._filters.remove(f)
        self._filter_index.pop(f.filter_id)

        def remove_filter_from_page(p: FilterPage):
            try:
                p.filters.remove(f)
            except ValueError:
                pass
            for pc in p.child_pages:
                remove_filter_from_page(pc)
        for p in self.pages:
            remove_filter_from_page(p)

    def notify_about_filter_rename_action(self, sender: Filter, old_id: str):
        self._filter_index.pop(old_id)
        self._filter_index[sender.filter_id] = sender
        for page in self._ui_pages:
            for widget in page.widgets:
                widget.notify_id_rename(old_id, sender.filter_id)
