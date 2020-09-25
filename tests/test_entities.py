import inspect

import attr
import pytest

from authalligator_client.entities import OMITTED, BaseAAEntity, entity_converter


@attr.attrs(frozen=True)
class TypeA(BaseAAEntity):
    TYPENAME = "TypeA"

    common = attr.attrib(default=OMITTED)
    a = attr.attrib(default=OMITTED)


@attr.attrs(frozen=True)
class TypeB(BaseAAEntity):
    TYPENAME = "TypeB"

    common = attr.attrib(default=OMITTED)
    b = attr.attrib(default=OMITTED)


@attr.attrs(frozen=True)
class TypeC(BaseAAEntity):
    TYPENAME = "TypeC"

    b = attr.attrib(
        default=OMITTED,
        converter=entity_converter(TypeB),  # type: ignore[misc]
    )


@attr.attrs(frozen=True)
class TypeD(BaseAAEntity):
    TYPENAME = "TypeD"

    inner = attr.attrib(
        default=OMITTED,
        converter=entity_converter([TypeA, TypeB]),  # type: ignore[misc]
    )


@pytest.mark.parametrize(
    "return_type,input_dict,output",
    [
        # a single type option
        (TypeA, {"common": "asdf"}, TypeA(common="asdf")),
        (TypeA, {"common": "asdf", "a": "a"}, TypeA(common="asdf", a="a")),
        (
            TypeA,
            {"__typename": "TypeA", "common": "asdf", "a": "a"},
            TypeA(common="asdf", a="a"),
        ),
        (TypeA, {"__typename": "TypeB", "common": "asdf"}, TypeError),
        # multiple type options
        ([TypeA, TypeB], {"common": "asdf", "a": "a"}, TypeError),
        (
            [TypeA, TypeB],
            {"__typename": "TypeA", "common": "asdf"},
            TypeA(common="asdf"),
        ),
        (
            [TypeA, TypeB],
            {"__typename": "TypeA", "common": "asdf", "a": "a"},
            TypeA(common="asdf", a="a"),
        ),
        (
            [TypeA, TypeB],
            {"__typename": "TypeB", "common": "asdf", "b": "b"},
            TypeB(common="asdf", b="b"),
        ),
        (
            [TypeA, TypeB],
            {"__typename": "TypeA", "common": "asdf", "b": "b"},
            TypeError,
        ),
        (
            [TypeA, TypeB],
            {"__typename": "TypeC", "common": "asdf"},
            TypeError,
        ),
        # nested converters, single option
        (
            TypeC,
            {"__typename": "TypeC", "b": {"common": "asdf"}},
            TypeC(b=TypeB(common="asdf")),
        ),
        (
            TypeC,
            {
                "__typename": "TypeC",
                "b": {"__typename": "TypeA", "common": "asdf"},
            },
            TypeError,
        ),
        # nested converter, multiple options
        (
            TypeD,
            {
                "__typename": "TypeD",
                "inner": {"__typename": "TypeA", "common": "asdf"},
            },
            TypeD(inner=TypeA(common="asdf")),
        ),
        (
            TypeD,
            {
                "__typename": "TypeD",
                "inner": {"__typename": "TypeA", "common": "asdf", "a": "a"},
            },
            TypeD(inner=TypeA(common="asdf", a="a")),
        ),
    ],
)
def test_entity_converter(return_type, input_dict, output):
    converter = entity_converter(return_type)

    if inspect.isclass(output) and issubclass(output, Exception):
        with pytest.raises(output):
            converter(input_dict)
    else:
        result = converter(input_dict)
        assert output == result


def test_from_api_response_snake_case():
    @attr.attrs(frozen=True)
    class TypeE(BaseAAEntity):
        TYPENAME = "TypeE"

        snake_case_field = attr.attrib(default=OMITTED)

    expected = TypeE(snake_case_field="data")
    actual = TypeE.from_api_response({"snakeCaseField": "data"})
    assert expected == actual
