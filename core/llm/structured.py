import ast
import json
import re
import math
from typing import Iterable


STRICT_JSON_CONTRACT = """
\n\nOUTPUT FORMAT CONTRACT — MUST FOLLOW EXACTLY:
- Return exactly ONE valid JSON object and nothing else.
- No Markdown fences, commentary, preface, suffix, XML, YAML, or prose outside JSON.
- Use double-quoted JSON keys/strings. No trailing commas or comments.
- Complete and close every array/object. Never intentionally truncate JSON.
- Preserve the requested key names and value types from the response schema in the prompt.
- When information is unavailable, use an empty string, [] or {} matching the requested type; do not explain outside JSON.
"""


class StructuredOutputError(ValueError):
    pass


def _strip_code_fence(text:str)->str:
    text=(text or "").strip().lstrip("\ufeff")
    text=re.sub(r"^```(?:json|javascript|js)?\s*","",text,flags=re.I)
    text=re.sub(r"\s*```$","",text)
    return text.strip()


def _balanced_candidates(text:str):
    for start,ch in enumerate(text):
        if ch not in "{[":
            continue
        stack=[];in_string=False;escape=False
        for i in range(start,len(text)):
            c=text[i]
            if in_string:
                if escape:
                    escape=False
                elif c=="\\":
                    escape=True
                elif c=='"':
                    in_string=False
                continue
            if c=='"':
                in_string=True
                continue
            if c in "{[":
                stack.append(c)
            elif c in "}]":
                if not stack:
                    break
                opener=stack.pop()
                if (opener,c) not in (("{","}"),("[","]")):
                    break
                if not stack:
                    yield text[start:i+1]
                    break


def _local_json_variants(text:str):
    base=_strip_code_fence(text)
    seen=set()
    def emit(v):
        if v not in seen:
            seen.add(v);return v
    v=emit(base)
    if v is not None: yield v
    fixed=(base
           .replace("“",'"').replace("”",'"')
           .replace("‘","'").replace("’","'"))
    fixed=re.sub(r",\s*([}\]])",r"\1",fixed)
    v=emit(fixed)
    if v is not None: yield v
    for candidate in _balanced_candidates(fixed):
        v=emit(candidate)
        if v is not None: yield v


def _matches_json_type(value,expected:str)->bool:
    if expected=="string": return isinstance(value,str)
    if expected=="boolean": return isinstance(value,bool)
    if expected=="number": return isinstance(value,(int,float)) and not isinstance(value,bool)
    if expected=="integer": return isinstance(value,int) and not isinstance(value,bool)
    if expected=="array": return isinstance(value,list)
    if expected=="object": return isinstance(value,dict)
    if expected=="null": return value is None
    return True


def _resolve_local_ref(root_schema:dict,ref:str)->dict:
    if not ref.startswith("#/"):
        return {}
    current=root_schema
    for token in ref[2:].split("/"):
        token=token.replace("~1","/").replace("~0","~")
        if not isinstance(current,dict) or token not in current:
            return {}
        current=current[token]
    return current if isinstance(current,dict) else {}


def _validate_value(value,schema:dict|None,path="$",root_schema:dict|None=None):
    if not schema:
        return
    root_schema=root_schema or schema
    if "$ref" in schema:
        resolved=_resolve_local_ref(root_schema,str(schema["$ref"]))
        if not resolved:
            raise StructuredOutputError(f"Field {path} has unresolved schema reference {schema['$ref']}")
        schema={**resolved,**{k:v for k,v in schema.items() if k!="$ref"}}
    alternatives=schema.get("anyOf") or schema.get("oneOf")
    if alternatives:
        failures=[]
        for option in alternatives:
            try:
                _validate_value(value,option,path,root_schema)
                break
            except StructuredOutputError as exc:
                failures.append(str(exc))
        else:
            raise StructuredOutputError(f"Field {path} did not match any allowed schema: {'; '.join(failures[:3])}")
    expected=schema.get("type")
    if isinstance(expected,list):
        if not any(_matches_json_type(value,t) for t in expected):
            raise StructuredOutputError(f"Field {path} expected {expected}, got {type(value).__name__}")
    elif isinstance(expected,str) and not _matches_json_type(value,expected):
        raise StructuredOutputError(f"Field {path} expected {expected}, got {type(value).__name__}")

    if "enum" in schema and value not in schema.get("enum",[]):
        raise StructuredOutputError(f"Field {path} expected one of {schema.get('enum')}, got {value!r}")
    if "const" in schema and value != schema.get("const"):
        raise StructuredOutputError(f"Field {path} expected constant {schema.get('const')!r}")
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        if not math.isfinite(float(value)):
            raise StructuredOutputError(f"Field {path} must be a finite number")
        if schema.get("minimum") is not None and value < float(schema["minimum"]):
            raise StructuredOutputError(f"Field {path} must be >= {schema['minimum']}, got {value}")
        if schema.get("maximum") is not None and value > float(schema["maximum"]):
            raise StructuredOutputError(f"Field {path} must be <= {schema['maximum']}, got {value}")
        if schema.get("exclusiveMinimum") is not None and value <= float(schema["exclusiveMinimum"]):
            raise StructuredOutputError(f"Field {path} must be > {schema['exclusiveMinimum']}, got {value}")
        if schema.get("exclusiveMaximum") is not None and value >= float(schema["exclusiveMaximum"]):
            raise StructuredOutputError(f"Field {path} must be < {schema['exclusiveMaximum']}, got {value}")
    if isinstance(value,str):
        if schema.get("minLength") is not None and len(value) < int(schema["minLength"]):
            raise StructuredOutputError(f"Field {path} is shorter than {schema['minLength']} characters")
        if schema.get("maxLength") is not None and len(value) > int(schema["maxLength"]):
            raise StructuredOutputError(f"Field {path} is longer than {schema['maxLength']} characters")
        if schema.get("pattern") is not None and not re.search(schema["pattern"],value):
            raise StructuredOutputError(f"Field {path} does not match required pattern")

    if expected=="object" and isinstance(value,dict):
        required=schema.get("required") or []
        missing=[k for k in required if k not in value]
        if missing:
            raise StructuredOutputError(f"Field {path} missing required keys: {', '.join(missing)}")
        properties=schema.get("properties") or {}
        for key,definition in properties.items():
            if key in value:
                _validate_value(value[key],definition,f"{path}.{key}",root_schema)
        additional=schema.get("additionalProperties",True)
        if additional is False:
            extras=[key for key in value if key not in properties]
            if extras:
                raise StructuredOutputError(f"Field {path} has unexpected keys: {', '.join(extras)}")
        elif isinstance(additional,dict):
            for key,item in value.items():
                if key not in properties:
                    _validate_value(item,additional,f"{path}.{key}",root_schema)
    elif expected=="array" and isinstance(value,list):
        if schema.get("minItems") is not None and len(value)<int(schema["minItems"]):
            raise StructuredOutputError(f"Field {path} expected at least {schema['minItems']} items")
        if schema.get("maxItems") is not None and len(value)>int(schema["maxItems"]):
            raise StructuredOutputError(f"Field {path} expected at most {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            seen=set()
            for item in value:
                marker=json.dumps(item,sort_keys=True,ensure_ascii=False) if isinstance(item,(dict,list)) else repr(item)
                if marker in seen:
                    raise StructuredOutputError(f"Field {path} must contain unique items")
                seen.add(marker)
        item_schema=schema.get("items")
        if item_schema:
            for i,item in enumerate(value):
                _validate_value(item,item_schema,f"{path}[{i}]",root_schema)


def _validate_schema(data:dict,schema:dict|None):
    if not schema:
        return
    _validate_value(data,schema,"$",schema)


def _object_shapes(data:dict,required:tuple[str,...]):
    """Yield the object itself, then one unambiguous provider/model wrapper.

    Some OpenAI-compatible gateways and models return
    ``{"result": {...contract...}}`` even when JSON-object mode is requested.
    Unwrapping is safe only when exactly one nested object contains every
    required top-level key. Semantic/schema validation still runs afterwards.
    """
    yield data
    if not required or all(key in data for key in required):
        return
    matches=[];seen=set()
    for value in data.values():
        if not isinstance(value,dict) or not all(key in value for key in required):
            continue
        marker=id(value)
        if marker not in seen:
            seen.add(marker);matches.append(value)
    if len(matches)==1:
        yield matches[0]


def parse_json_object(text:str,required:Iterable[str]=(),schema:dict|None=None,
                      list_field:str="",list_defaults:dict|None=None):
    required=tuple(required)
    last_error=None
    for candidate in _local_json_variants(text):
        try:
            data=json.loads(candidate,strict=False)
        except Exception as exc:
            last_error=exc
            try:
                data=ast.literal_eval(candidate)
            except Exception:
                continue
        if isinstance(data,dict):
            shapes=_object_shapes(data,required)
        elif isinstance(data,list):
            # Some search-enabled gateways wrap the one requested unit object
            # in a JSON array despite response_format=json_object. Unwrap only
            # when exactly one object satisfies the complete root contract.
            matches=[item for item in data if isinstance(item,dict) and all(k in item for k in required)]
            if len(matches)==1:
                shapes=iter(matches)
            elif not data and list_field:
                # An empty provider array contains no contract object to unwrap.
                # Callers that explicitly opt into list normalization provide
                # the root defaults needed to build a schema-valid empty result.
                wrapped=dict(list_defaults or {});wrapped[list_field]=[];shapes=iter([wrapped])
            elif not matches and list_field and all(isinstance(item,dict) for item in data):
                wrapped=dict(list_defaults or {});wrapped[list_field]=data;shapes=iter([wrapped])
            else:
                last_error=TypeError(f"Expected one contract object, got list with {len(matches)} matches")
                continue
        else:
            last_error=TypeError(f"Expected JSON object, got {type(data).__name__}")
            continue
        for shaped in shapes:
            missing=[k for k in required if k not in shaped]
            if missing:
                last_error=KeyError(f"Missing required keys: {', '.join(missing)}")
                continue
            try:
                _validate_schema(shaped,schema)
            except StructuredOutputError as exc:
                last_error=exc
                continue
            return shaped
    raise StructuredOutputError(str(last_error or "Could not parse a JSON object"))
