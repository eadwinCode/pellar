import pytest
from pydantic.fields import ModelField

from ellar.core.response.model import ResponseModelField
from ellar.helper.modelfield import create_model_field


def test_create_model_field_works():
    response_model = create_model_field(
        name="response_model",
        type_=dict,
        model_field_class=ResponseModelField,
    )
    assert isinstance(response_model, ModelField)
    assert response_model.outer_type_ == dict
    assert response_model.type_ == dict


def test_create_model_field_fails():
    with pytest.raises(
        Exception,
        match="Invalid args for response field! Hint: check that whatever is a valid pydantic field type",
    ):
        create_model_field(
            name="response_model",
            type_="whatever",
        )
