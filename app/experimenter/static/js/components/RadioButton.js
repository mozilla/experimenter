import React from "react";
import { Row, Col, Form } from "react-bootstrap";
import PropTypes from "prop-types";
import { List, Map } from "immutable";

export default class RadioButton extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    handleBranchedAddonRadio: PropTypes.func,
  };

  constructor(props) {
    super(props);
  }

  render() {
    return (
      <Row>
        <Col md={{ span: 9, offset: 3 }}>
          <Form.Group className="mb-3">
            <Form.Row>
              <Form.Label>
                <strong>
                  {this.props.elementLabel}
                </strong>
              </Form.Label>
            </Form.Row>

            <Form.Check
              inline
              value={this.props.radioValue1}
              defaultChecked={!this.props.data.get("is_branched_addon")}
              label={this.props.radioLabel1}
              type="radio"
              onChange={this.props.handleBranchedAddonRadio}
              name={this.props.radioGroupName}
            />
            <Form.Check
              inline
              label={this.props.radioLabel2}
              value={this.props.radioValue2}
              defaultChecked={this.props.data.get("is_branched_addon")}
              type="radio"
              onChange={this.props.handleBranchedAddonRadio}
              name={this.props.radioGroupName}
            />
          </Form.Group>
        </Col>
      </Row>
    )
  }
}
