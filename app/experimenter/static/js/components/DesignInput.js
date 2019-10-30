import React from "react";
import ReactDOM from "react-dom";
import {
  Button,
  Container,
  Row,
  Col,
  FormControl,
  FormLabel
} from "react-bootstrap";
import { boundMethod } from "autobind-decorator";

import Error from "experimenter/components/Error";
import HelpBox from "experimenter/components/HelpBox";

export default class DesignInput extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      value: this.props.value,
      help_showing: false
    };
  }

  @boundMethod
  toggleHelp(e) {
    this.setState({ help_showing: !this.state.help_showing });
  }

  @boundMethod
  updateValue(e) {
    this.setState({ value: e.target.value });
  }

  render() {
    return (
      <Row className={this.props.margin}>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>{this.props.label}</strong>
          </FormLabel>
          <br />
          <a
            href="#"
            name={this.props.name}
            data-index={this.props.index}
            onClick={this.toggleHelp}
          >
            Help
          </a>
        </Col>
        <Col md={9}>
          <FormControl
            as={this.props.as}
            rows={this.props.rows}
            data-index={this.props.index}
            id={this.props.id}
            type="text"
            name={this.props.name}
            onChange={this.updateValue}
            value={this.state.value}
            className={this.props.error ? "is-invalid" : ""}
          >
            {this.props.children}
          </FormControl>
          {this.props.error ? <Error error={this.props.error} /> : ""}
          <HelpBox showing={this.state.help_showing}>
            {this.props.helpContent}
          </HelpBox>
        </Col>
      </Row>
    );
  }
}
