"""Scene module"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .filter import Filter

if TYPE_CHECKING:
    from .board_configuration import BoardConfiguration
    from .control_desk import BankSet
    from .ui_configuration import UIPage


class FilterPage:
    """Filter page in a Scene"""

    def __init__(self, parent: Scene):
        self._filters: list[Filter] = []
        self._child_pages: list[FilterPage] = []
        self._parent_scene: Scene = parent
        self._name: str = ""

    @property
    def name(self) -> str:
        """name"""
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = str(new_name)

    @property
    def filters(self) -> list[Filter]:
        """list of filters"""
        return self._filters

    @property
    def child_pages(self) -> list[FilterPage]:
        """list of child pages"""
        return self._child_pages

    @property
    def parent_scene(self) -> Scene:
        """parent scene"""
        return self._parent_scene

    def copy(self, new_scene: Scene = None):
        """copy of a filter page"""
        if not new_scene:
            new_fp = FilterPage(self._parent_scene)
            # Internal copying should not copy filters as they are unique within Scene
        else:
            new_fp = FilterPage(new_scene)
            for filter_ in self._filters:
                found_filter = new_scene.get_filter_by_id(filter_.filter_id)
                if found_filter:
                    new_fp._filters.append(found_filter)
        for child_fp in self._child_pages:
            new_fp._child_pages.append(child_fp.copy(new_scene))
        new_fp._name = self.name
        return new_fp


class Scene:
    """Scene for a show file."""

    def __init__(self, scene_id: int,
                 human_readable_name: str,
                 board_configuration: BoardConfiguration):
        self._scene_id: int = scene_id
        self._human_readable_name: str = human_readable_name
        self._board_configuration: BoardConfiguration = board_configuration
        self._filters: list[Filter] = []
        self._filter_index: dict[str, Filter] = {}
        self._filter_pages: list[FilterPage] = []
        self._associated_bankset: BankSet | None = None
        self._ui_pages: list[UIPage] = []

    @property
    def scene_id(self) -> int:
        """The unique id of the scene"""
        return self._scene_id

    @property
    def human_readable_name(self) -> str:
        """The human-readable name of the scene displayed by the ui"""
        return self._human_readable_name

    @human_readable_name.setter
    def human_readable_name(self, human_readable_name: str):
        """Sets the human-readable name of the scene displayed by the ui"""
        self._human_readable_name = human_readable_name

    @property
    def board_configuration(self) -> BoardConfiguration:
        """The board configuration the scene is part of"""
        return self._board_configuration

    @property
    def filters(self) -> list[Filter]:
        """The filters of the scene. Warning: do not use this to call append on it. Use scene.append_filter instead."""
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
        """
        add a filterpage to the scene
        """
        self._filter_pages.append(fp)

    @property
    def linked_bankset(self) -> BankSet | None:
        """associated_bankset"""
        return self._associated_bankset

    @linked_bankset.setter
    def linked_bankset(self, new_bs: BankSet):
        if self._associated_bankset:
            if self._associated_bankset.is_linked:
                self._associated_bankset.unlink()
        self._associated_bankset = new_bs

    @property
    def ui_pages(self) -> list[UIPage]:
        """list of UIPages"""
        return self._ui_pages

    def __str__(self) -> str:
        if self.human_readable_name:
            return self.human_readable_name
        return str(self._scene_id)

    def ensure_bankset(self) -> bool:
        """This method makes sure that the bank set associated with this scene gets applied to fish."""
        if self._associated_bankset is None:
            from .control_desk import BankSet
            self._associated_bankset = BankSet(description=f"Bankset associated with scene {self._scene_id}.",
                                               gui_controlled=True)
            return False
        return True

    def copy(self, existing_scenes: list[Scene]) -> Scene:
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
        """get filter by filter ID"""
        f = self._filter_index.get(fid)
        if f:
            return f
        for f in self._filters:
            if f.filter_id == fid:
                self._filter_index[fid] = f
                return f
        return None

    def ensure_name_uniqueness(self, name_to_try: str) -> str:
        """This method checks the provided name for uniqueness within this scene.
        :param name_to_try: The name to check for uniqueness
        :returns: A minimal modified version of the provided name that ensures uniqueness.
        """
        while self.get_filter_by_id(name_to_try):
            name_appendix = ""
            while name_to_try[-1].isdigit():
                name_appendix = name_to_try[-1]
                name_to_try = name_to_try[:-1]
            if name_appendix == "":
                name_appendix = "0"
            name_to_try += str(int(name_appendix) + 1)
        return name_to_try

    def append_filter(self, f: Filter, filter_page_index: int = -1):
        """
        Insert a filter in the scene.
        :param f: The filter to add
        :param filter_page_index: The index of the filter page to add it to.
                                  -1 indicates that this step should be skipped.
        """
        if f.scene and f.scene != self:
            raise Exception(f"This filter ({f.filter_id}) is already added to a scene other than this one")
        if f.scene == self and f in self.filters:
            return
        f.filter_id = self.ensure_name_uniqueness(f.filter_id)
        self._filters.append(f)
        self._filter_index[f.filter_id] = f
        if filter_page_index != -1:
            if filter_page_index < len(self.pages):
                self._filter_pages[filter_page_index].filters.append(f)

    def remove_filter(self, f: Filter):
        """Delete a filter."""
        self._filters.remove(f)
        if self._filter_index.get(f.filter_id):
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
        """
        This method checks connections of a filter which should be renamed and updates them accordingly.
        :param sender: The filter that was renamed
        :param old_id: The id which this filter was known as before.
        """
        if self._filter_index.get(old_id):
            self._filter_index.pop(old_id)
        self._filter_index[sender.filter_id] = sender
        for page in self._ui_pages:
            for widget in page.widgets:
                widget.notify_id_rename(old_id, sender.filter_id)
