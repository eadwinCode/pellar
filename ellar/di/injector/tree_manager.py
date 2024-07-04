import typing as t
from weakref import WeakKeyDictionary

from ellar.di.service_config import (
    ProviderConfig,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import (
        ModuleRefBase,
        ModuleSetup,
    )


class TreeData(t.NamedTuple):
    value: t.Union["ModuleRefBase", "ModuleSetup"]
    parent: t.Optional[t.Type]
    dependencies: t.List[t.Type]

    @property
    def is_ready(self) -> bool:
        return self.value.is_ready

    @property
    def ref_type(self) -> str:
        return self.value.ref_type

    @property
    def exports(self) -> t.List[t.Type]:
        return self.value.exports

    @property
    def providers(self) -> t.Dict[t.Type, t.Type]:
        return self.value.providers

    @property
    def name(self) -> str:
        return self.value.name

    def __repr__(self) -> str:
        return f"module={self.value.module} name={self.value.name} ref_type={self.ref_type}"

    def __str__(self) -> str:
        return self.__repr__()


class ModuleTreeManager:
    __slots__ = ("modules", "_core_module", "_root_module")

    # , root_module: t.Union["ModuleRefBase", "ModuleSetup"]
    def __init__(
        self,
        app_core_module: t.Optional[t.Union["ModuleRefBase", "ModuleSetup"]] = None,
    ) -> None:
        self.modules: t.MutableMapping[t.Type, TreeData] = (
            WeakKeyDictionary()
        )  # Dictionary to store modules by their ID or value

        self._core_module = app_core_module.module if app_core_module else None
        self._root_module: t.Optional[t.Type[t.Any]] = None

        if app_core_module:
            self.add_module(app_core_module.module, value=app_core_module)

    @property
    def root_module(self) -> t.Type:
        assert self._root_module is not None, "RootModule is not ready"
        return self._root_module

    def add_provider(
        self,
        module_type: t.Type,
        provider_type: t.Union[t.Type, ProviderConfig],
        export: bool = False,
    ) -> "ModuleTreeManager":
        data = self.get_module(module_type)

        if data is None:
            raise ValueError(f"Module {module_type} does not exists. Use 'add_module'")

        if data.is_ready:
            data.value.add_provider(provider_type, export=export)
        return self

    def add_module(
        self,
        module_type: t.Type,
        value: t.Union["ModuleRefBase", "ModuleSetup"],
        parent_module: t.Optional[t.Type] = None,
    ) -> "ModuleTreeManager":
        if module_type in self.modules:
            raise ValueError(
                f"Module {module_type} already exists. Use 'update_module'"
            )

        data = TreeData(value=value, parent=parent_module, dependencies=[])

        self.modules[module_type] = data

        if parent_module:
            if parent_module not in self.modules:
                raise ValueError(
                    f"Parent data for Module {parent_module} does not exist."
                )

            self.modules[parent_module].dependencies.append(module_type)

            if parent_module == self._core_module and not self._root_module:
                self._root_module = data.value.module

        elif not parent_module and not self._root_module and not self._core_module:
            self._root_module = module_type
        elif (
            self._root_module
            and parent_module
            and self._core_module
            and parent_module == self._core_module
        ):
            raise Exception(
                f"EllarCoreModule can only have '{self._root_module}' as dependency"
            )
        return self

    def add_module_dependency(
        self,
        parent_module: t.Type,
        dependency: t.Type,
    ) -> None:
        data = self.get_module(parent_module)
        if data is None:
            raise ValueError(
                f"Trying to add module dependency, Module {parent_module} does not exists."
            )

        data.dependencies.append(dependency)

    def update_module(
        self,
        module_type: t.Type,
        value: t.Union["ModuleRefBase", "ModuleSetup"],
        parent_module: t.Optional[t.Type] = None,
    ) -> "ModuleTreeManager":
        data = self.get_module(module_type)
        if data is None:
            raise ValueError(f"Module {module_type} does not exists. Use 'add_module'")

        new_module_data = TreeData(
            value=value,
            parent=parent_module or data.parent,
            dependencies=data.dependencies,
        )
        self.modules[module_type] = new_module_data
        return self

    def add_or_update(
        self,
        module_type: t.Type,
        value: t.Union["ModuleRefBase", "ModuleSetup"],
        parent_module: t.Optional[t.Type] = None,
    ) -> "ModuleTreeManager":
        try:
            self.add_module(module_type, value, parent_module)
        except ValueError:
            self.update_module(module_type, value, parent_module)
        return self

    def get_module(self, module_type: t.Type) -> t.Optional[TreeData]:
        return self.modules.get(module_type)

    def get_by_ref_type(self, ref_type: str) -> t.List[t.Union[TreeData, t.Any]]:
        return [v for k, v in self.modules.items() if v.ref_type == ref_type]

    def get_module_dependencies(
        self,
        parent_id: t.Type,
        predicate: t.Optional[t.Callable[[TreeData], bool]] = None,
    ) -> t.List[TreeData]:
        data = self.get_module(parent_id)
        if not data:
            return []

        if predicate is not None:
            return [
                child
                for child in (self.get_module(item) for item in data.dependencies)
                if child and predicate(child)
            ]

        return [
            child
            for child in (self.get_module(item) for item in data.dependencies)
            if child
        ]

    def find_module(
        self, predicate: t.Callable[[TreeData], bool]
    ) -> t.Iterator[TreeData]:
        found_any = False
        for _key, data in self.modules.items():
            if predicate(data):
                found_any = True
                yield data

        if not found_any:
            yield None  # type:ignore[misc]

    def get_root_module(self) -> t.Union["ModuleRefBase", "ModuleSetup"]:
        data = self.get_module(self.root_module)
        assert data
        return data.value

    def search_module_tree(
        self,
        filter_item: t.Callable[[TreeData], bool],
        find_predicate: t.Callable[[TreeData], bool],
    ) -> t.Optional[TreeData]:
        """
        Searches for a node by defined predicate using DFS.

        :param filter_item:
        :param find_predicate:
        :return: The node with the given ID, or None if not found.
        """

        def dfs(current_node: TreeData) -> t.Optional[TreeData]:
            if find_predicate(current_node):
                return current_node

            for child_id in current_node.dependencies:
                child_node = self.get_module(child_id)
                if child_node:
                    res = dfs(child_node)
                    if res:
                        return res
            return None

        # Start DFS from each root node in the tree (nodes with no parents)
        for module in self.find_module(filter_item):
            result = dfs(module)
            if result:
                return result
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return str(self.modules)
