import { boundClass } from "autobind-decorator";
import PropTypes from "prop-types";
import React from "react";
import { Form, Row, Col } from "react-bootstrap";

import Error from "experimenter/components/Error";
import HelpBox from "experimenter/components/HelpBox";

@boundClass
class RadioButtonInlineLabel extends React.PureComponent {
  static propTypes = {
    elementLabel: PropTypes.string,
    fieldName: PropTypes.string,
    onChange: PropTypes.func,
    choices: PropTypes.arrayOf(PropTypes.object),
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
    optional: PropTypes.bool,
    noHelpLink: PropTypes.bool,
    helpIsExternalLink: PropTypes.bool,
    helpContent: PropTypes.string,
    name: PropTypes.string,
    error: PropTypes.string,
    id: PropTypes.string,
    index: PropTypes.number,
  };

  constructor(props) {
    super(props);

    this.state = {
      help_showing: false,
    };
  }

  toggleHelp(e) {
    e.preventDefault();
    this.setState({ help_showing: !this.state.help_showing });
  }

  displayRequiredOrOptional() {
    if (this.props.optional) {
      return (
        <div className="required-label optional">
          <div className="text-muted">Optional</div>
        </div>
      );
    } else {
      return (
        <div className="required-label required">
          <div className="text-danger">Required</div>
        </div>
      );
    }
  }

  showHelpLink() {
    if (!this.props.noHelpLink) {
      if (this.props.helpIsExternalLink) {
        return (
          <a
            target="_blank"
            rel="noreferrer noopener"
            href={this.props.helpContent}
          >
            Help
          </a>
        );
      } else {
        return (
          <div>
            <a
              href="#"
              name={this.props.name}
              data-index={this.props.index}
              onClick={this.toggleHelp}
            >
              Help
            </a>
          </div>
        );
      }
    }
  }

  render() {
    return (
      <Row className="mb-2">
        <Col md={2} className="text-right">
          <Form.Label for={this.props.id}>
            <strong>{this.props.elementLabel}</strong>
            {this.displayRequiredOrOptional()}
          </Form.Label>
          <div>{this.showHelpLink()}</div>
        </Col>
        <Col>
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
              inline={true}
            />
          ))}
          {this.props.error ? <Error error={this.props.error} /> : null}
          <HelpBox showing={this.state.help_showing}>
            {this.props.helpContent}
          </HelpBox>
        </Col>
      </Row>
    );
  }
}

export default RadioButtonInlineLabel;
