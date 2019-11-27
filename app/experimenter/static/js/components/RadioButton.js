import PropTypes from "prop-types";
import React from "react";
import { Row, Col, Form } from "react-bootstrap";

export default class RadioButton extends React.PureComponent {
  static propTypes = {
    elementLabel: PropTypes.string,
    onChange: PropTypes.func,
    radioGroupName: PropTypes.string,
    radioLabel1: PropTypes.string,
    radioLabel2: PropTypes.string,
    radioValue1: PropTypes.string,
    radioValue2: PropTypes.string,
    value: PropTypes.bool,
  };

  constructor(props) {
    super(props);
  }

  handleRadioChange(event) {
    this.props.onChange(event.target.value === "true");
  }

  render() {
    return (
      <Row>
        <Col md={{ span: 9, offset: 3 }}>
          <Form.Group className="mb-3">
            <Form.Row>
              <Form.Label>
                <strong>{this.props.elementLabel}</strong>
              </Form.Label>
            </Form.Row>

            <Form.Check
              inline
              value={this.props.radioValue1}
              defaultChecked={!this.props.value}
              label={this.props.radioLabel1}
              type="radio"
              onChange={e => this.handleRadioChange(e)}
              name={this.props.radioGroupName}
            />
            <Form.Check
              inline
              label={this.props.radioLabel2}
              value={this.props.radioValue2}
              defaultChecked={this.props.value}
              type="radio"
              onChange={e => this.handleRadioChange(e)}
              name={this.props.radioGroupName}
            />
          </Form.Group>
        </Col>
      </Row>
    );
  }
}
