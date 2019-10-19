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
import PrefValueInput from "pref-value-input";
import TypeForm from "type-form";
import Error from "error-form";
import HelpBox from "help-box";


export default class DesignInput extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      help_showing: false
    }
  }

  @boundMethod
  toggleHelp(e) {
    this.setState({help_showing: !this.state.help_showing});
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
            help
          </a>
        </Col>
        <Col md={9}>
          <FormControl
            as={this.props.as}
            rows={this.props.rows}
            data-index={this.props.index}
            id={"variants-" + this.props.index + "-" + this.props.name}
            type="text"
            name={this.props.name}
            onChange={this.props.handleInputChange}
            value={this.props.value}
            className={this.props.error ? "is-invalid" : ""}
          />
          {this.props.error ? (<Error error={this.props.error} />) : ("")}
          <HelpBox showing={this.state.help_showing}>
            {this.props.helpContent}
          </HelpBox>
        </Col>
      </Row>
    )
  }
}
