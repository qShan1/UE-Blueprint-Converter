import re
from .models import BlueprintGraph, NodeInfo, PinInfo, VariableRef


class BlueprintParser:
    def __init__(self) -> None:
        pass

    def parse(self, text: str) -> BlueprintGraph:
        raw_objects = self._parse_raw_objects(text)
        nodes = []
        for obj in raw_objects:
            node = self._object_to_node(obj)
            if node is not None:
                nodes.append(node)
        exec_flow, data_flow = self._build_connections(nodes)
        return BlueprintGraph(nodes=nodes, exec_flow=exec_flow, data_flow=data_flow)

    def _parse_raw_objects(self, text: str) -> list[dict]:
        lines = text.split("\n")
        objects, _ = self._parse_blocks(lines, 0)
        return objects

    def _parse_blocks(self, lines: list[str], start: int) -> tuple[list[dict], int]:
        objects = []
        i = start
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith("End Object"):
                break
            if line.startswith("Begin Object"):
                obj, i = self._parse_single_object(lines, i)
                objects.append(obj)
            else:
                i += 1
        return objects, i

    def _parse_single_object(self, lines: list[str], start: int) -> tuple[dict, int]:
        header = lines[start].strip()
        class_path, name = self._parse_object_header(header)
        obj: dict = {
            "class_path": class_path,
            "name": name,
            "properties": {},
            "children": [],
        }
        i = start + 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith("End Object"):
                i += 1
                break
            if line.startswith("Begin Object"):
                child, i = self._parse_single_object(lines, i)
                obj["children"].append(child)
                continue
            key, value, consumed = self._parse_property_line(lines, i)
            if key is not None:
                if isinstance(value, list):
                    obj["children"].extend(value)
                    obj["properties"][key] = value
                else:
                    obj["properties"][key] = value
            i = consumed if consumed > i else i + 1
        return obj, i

    def _parse_object_header(self, line: str) -> tuple[str, str]:
        class_match = re.search(r"Class=(\S+)", line)
        name_match = re.search(r'Name="([^"]*)"', line)
        class_path = class_match.group(1) if class_match else ""
        name = name_match.group(1) if name_match else ""
        return class_path, name

    def _parse_property_line(
        self, lines: list[str], start: int
    ) -> tuple[str | None, str | list[dict] | None, int]:
        line = lines[start].strip()
        eq_idx = line.find("=")
        if eq_idx == -1:
            return None, None, start
        key = line[:eq_idx].strip()
        value_str = line[eq_idx + 1 :].strip()

        if value_str.startswith("(Begin Object"):
            inner_objects, end_idx = self._parse_parenthesized_blocks(
                lines, start, eq_idx
            )
            return key, inner_objects, end_idx

        cleaned = self._clean_value(value_str)
        return key, cleaned, start

    def _parse_parenthesized_blocks(
        self, lines: list[str], start: int, eq_idx: int
    ) -> tuple[list[dict], int]:
        first_line = lines[start].strip()
        paren_content = first_line[eq_idx + 1 :]
        if paren_content.startswith("("):
            paren_content = paren_content[1:]

        paren_lines = []
        depth = 1
        consume_start = start

        if paren_content.strip():
            paren_lines.append(paren_content)

        i = start + 1
        while i < len(lines) and depth > 0:
            stripped = lines[i].strip()
            begin_count = stripped.count("Begin Object")
            end_count = stripped.count("End Object")

            if end_count > 0:
                depth -= end_count
                if depth <= 0:
                    before_paren = stripped
                    if before_paren.endswith(")"):
                        before_paren = before_paren[: -before_paren.count(")")]
                    if before_paren.strip():
                        paren_lines.append(before_paren.strip())
                    i += 1
                    break
            if begin_count > 0:
                depth += begin_count
            paren_lines.append(stripped)
            i += 1

        sub_objects, _ = self._parse_blocks(paren_lines, 0)
        return sub_objects, i

    def _clean_value(self, value: str) -> str:
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        if value == "None" or value == "":
            return ""
        if value.startswith("(") and value.endswith(")"):
            inner = value[1:-1].strip()
            if inner and not inner.startswith("Begin Object"):
                return inner
            return ""
        return value

    def _object_to_node(self, obj: dict) -> NodeInfo | None:
        class_path = obj["class_path"]
        name = obj["name"]

        if "K2Node" not in class_path and "EdGraphPin" not in class_path:
            return None

        if "EdGraphPin" in class_path:
            return None

        node_type = self._derive_node_type(class_path, obj["properties"])
        display_name = self._derive_display_name(name, node_type, obj["properties"])
        pins = self._extract_pins(obj["children"])
        variables = self._extract_variables(node_type, obj["properties"])

        metadata = {}
        for k, v in obj["properties"].items():
            if isinstance(v, str) and k not in (
                "NodePosX",
                "NodePosY",
                "NodeGuid",
                "bIsEnabled",
            ):
                metadata[k] = v

        return NodeInfo(
            name=name,
            node_type=node_type,
            raw_type=class_path,
            display_name=display_name,
            pins=pins,
            variables=variables,
            metadata=metadata,
        )

    def _derive_node_type(
        self, class_path: str, properties: dict
    ) -> str:
        if "K2Node_Event" in class_path:
            return properties.get("CustomFunctionName", "UnknownEvent")
        if "K2Node_IfThenElse" in class_path:
            return "Branch"
        if "K2Node_CallFunction" in class_path:
            func_ref = properties.get("FunctionReference", "")
            if "." in func_ref:
                func_ref = func_ref.rsplit(".", 1)[-1]
            return func_ref or "CallFunction"
        if "K2Node_VariableGet" in class_path:
            var_name = properties.get("VariableName", "Unknown")
            return f"{var_name} (Get)"
        if "K2Node_VariableSet" in class_path:
            var_name = properties.get("VariableName", "Unknown")
            return f"{var_name} (Set)"
        if "K2Node_ForEachLoop" in class_path:
            return "ForEachLoop"
        if "K2Node_ForLoop" in class_path:
            return "ForLoop"
        if "K2Node_MathExpression" in class_path:
            return "MathExpression"
        if "K2Node_Select" in class_path:
            return "Select"
        if "K2Node_Switch" in class_path:
            return "Switch"
        if "K2Node_DynamicCast" in class_path:
            return "DynamicCast"
        if "K2Node_ExecutionSequence" in class_path:
            return "ExecutionSequence"
        if "K2Node_InputAction" in class_path:
            action_name = properties.get("InputActionName", "UnknownAction")
            return f"InputAction ({action_name})"
        if "K2Node_InputAxis" in class_path:
            axis_name = properties.get("InputAxisName", "UnknownAxis")
            return f"InputAxis ({axis_name})"
        if "K2Node_CommutativeAssociativeBinaryOperator" in class_path:
            return "BinaryOperator"
        if "K2Node_CustomEvent" in class_path:
            return properties.get("CustomFunctionName", "CustomEvent")
        short = class_path.rsplit(".", 1)[-1] if "." in class_path else class_path
        return short

    def _derive_display_name(
        self, name: str, node_type: str, properties: dict
    ) -> str:
        node_name = properties.get("NodeName", "")
        if node_name:
            return node_name
        category = properties.get("Category", "")
        if category:
            return f"{category} | {node_type}"
        return node_type if node_type else name

    def _extract_pins(self, children: list[dict]) -> list[PinInfo]:
        pins = []
        for child in children:
            if "EdGraphPin" not in child.get("class_path", ""):
                continue
            props = child["properties"]
            pin_name = props.get("PinName", child.get("name", ""))
            raw_direction = props.get("PinDirection", "EGPD_Output")
            direction = "Input" if "EGPD_Input" in raw_direction else "Output"

            pin_type = self._extract_pin_type(props)

            linked_to_raw = props.get("LinkedTo", "")
            linked_to = []
            if isinstance(linked_to_raw, list):
                for ref_obj in linked_to_raw:
                    ref_name = ref_obj.get("name", "")
                    ref_props = ref_obj.get("properties", {})
                    linked_name = ref_props.get("PinName", ref_name)
                    if linked_name:
                        linked_to.append(linked_name)
            elif isinstance(linked_to_raw, str) and linked_to_raw:
                linked_to = [linked_to_raw]

            pins.append(
                PinInfo(
                    name=pin_name,
                    direction=direction,
                    pin_type=pin_type,
                    linked_to=linked_to,
                )
            )
        return pins

    def _extract_pin_type(self, props: dict) -> str:
        pin_category = props.get("PinType.PinCategory", props.get("PinCategory", ""))
        if pin_category:
            return pin_category
        for key in props:
            if "PinCategory" in key:
                val = props[key]
                if isinstance(val, str) and val:
                    return val
        return ""

    def _extract_variables(
        self, node_type: str, properties: dict
    ) -> list[VariableRef]:
        variables = []
        if "(Get)" in node_type:
            var_name = node_type.replace(" (Get)", "")
            var_type = properties.get("VariableType", "")
            variables.append(
                VariableRef(name=var_name, operation="read", var_type=var_type or None)
            )
        elif "(Set)" in node_type:
            var_name = node_type.replace(" (Set)", "")
            var_type = properties.get("VariableType", "")
            variables.append(
                VariableRef(
                    name=var_name, operation="write", var_type=var_type or None
                )
            )
        return variables

    def _build_connections(
        self, nodes: list[NodeInfo]
    ) -> tuple[list[tuple[str, str, int]], list[tuple[str, str, str, str]]]:
        exec_flow: list[tuple[str, str, int]] = []
        data_flow: list[tuple[str, str, str, str]] = []

        pin_map_by_name: dict[str, list[tuple[str, PinInfo]]] = {}
        for node in nodes:
            for pin in node.pins:
                if pin.name not in pin_map_by_name:
                    pin_map_by_name[pin.name] = []
                pin_map_by_name[pin.name].append((node.name, pin))

        for node in nodes:
            for pin in node.pins:
                for linked_name in pin.linked_to:
                    targets = pin_map_by_name.get(linked_name, [])
                    for target_node_name, target_pin in targets:
                        if target_node_name == node.name:
                            continue
                        if pin.pin_type == "exec" and pin.direction == "Output":
                            exec_flow.append(
                                (node.name, target_node_name, len(exec_flow))
                            )
                        elif pin.pin_type != "exec" and pin.direction == "Output":
                            data_flow.append(
                                (
                                    node.name,
                                    pin.name,
                                    target_node_name,
                                    target_pin.name,
                                )
                            )

        seen_exec = set()
        unique_exec = []
        for item in exec_flow:
            key = (item[0], item[1])
            if key not in seen_exec:
                seen_exec.add(key)
                unique_exec.append(item)
        exec_flow = unique_exec

        seen_data = set()
        unique_data = []
        for item in data_flow:
            key = (item[0], item[1], item[2], item[3])
            if key not in seen_data:
                seen_data.add(key)
                unique_data.append(item)
        data_flow = unique_data

        return exec_flow, data_flow