import PropTypes from "prop-types";
import React from "react";
import { Form } from "react-bootstrap";

export default class RadioButton extends React.PureComponent {
  static propTypes = {
    elementLabel: PropTypes.string,
    fieldName: PropTypes.string,
    onChange: PropTypes.func,
    choices: PropTypes.arrayOf(PropTypes.object),
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
  };

  render() {
    return (
      <Form.Group className="mb-4">
        <Form.Row>
          <Form.Label>
            <h5>{this.props.elementLabel}</h5>
          </Form.Label>
        </Form.Row>

        {this.props.choices.map(({ label, value }) => (
          <Form.Check
            key={value}
            className="mb-2"
            defaultChecked={this.props.value === value}
            id={`${this.props.fieldName}-${value}`}
            label={`${label}`}
            name={this.props.fieldName}
            onChange={this.props.onChange}
            type="radio"
            value={value}
          />
        ))}
      </Form.Group>
    );
  }
}
