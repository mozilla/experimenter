import PropTypes from "prop-types";
import React from "react";
import { Form } from "react-bootstrap";

export default class RadioButton extends React.PureComponent {
  static propTypes = {
    elementLabel: PropTypes.string,
    fieldName: PropTypes.string,
    onChange: PropTypes.func,
    radioLabel1: PropTypes.string,
    radioLabel2: PropTypes.string,
    radioValue1: PropTypes.string,
    radioValue2: PropTypes.string,
    value: PropTypes.bool,
  };

  handleRadioChange(event) {
    this.props.onChange(event.target.value === "true");
  }

  render() {
    return (
      <Form.Group>
        <Form.Row>
          <Form.Label>
            <h5>{this.props.elementLabel}</h5>
          </Form.Label>
        </Form.Row>

        <Form.Check
          className="mb-2"
          defaultChecked={!this.props.value}
          id={`${this.props.fieldName}-${this.props.radioValue1}`}
          label={`${this.props.radioLabel1}`}
          name={this.props.fieldName}
          onChange={e => this.handleRadioChange(e)}
          type="radio"
          value={this.props.radioValue1}
        />

        <Form.Check
          className="mb-2"
          defaultChecked={this.props.value}
          id={`${this.props.fieldName}-${this.props.radioValue2}`}
          label={`${this.props.radioLabel2}`}
          name={this.props.fieldName}
          onChange={e => this.handleRadioChange(e)}
          type="radio"
          value={this.props.radioValue2}
        />
      </Form.Group>
    );
  }
}
