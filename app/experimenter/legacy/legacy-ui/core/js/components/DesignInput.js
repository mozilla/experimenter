import { boundClass } from "autobind-decorator";
import Error from "experimenter/components/Error";
import HelpBox from "experimenter/components/HelpBox";
import PropTypes from "prop-types";
import React from "react";
import { Col, FormControl, FormLabel, Row } from "react-bootstrap";

@boundClass
class DesignInput extends React.PureComponent {
  static propTypes = {
    as: PropTypes.string,
    children: PropTypes.oneOfType([
      PropTypes.arrayOf(PropTypes.node),
      PropTypes.node,
    ]),
    dataTestId: PropTypes.string,
    error: PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.array,
      PropTypes.object,
    ]),
    helpContent: PropTypes.object,
    id: PropTypes.string,
    index: PropTypes.number,
    labelColumnWidth: PropTypes.number,
    label: PropTypes.string,
    name: PropTypes.string,
    note: PropTypes.string,
    onChange: PropTypes.func,
    rows: PropTypes.string,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    type: PropTypes.string,
    optional: PropTypes.bool,
    noHelpLink: PropTypes.bool,
    helpIsExternalLink: PropTypes.bool,
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

  determineInputColumnWidth() {
    return 12 - this.props.labelColumnWidth;
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
      <Row className="mb-3">
        <Col md={this.props.labelColumnWidth} className="text-right">
          <FormLabel for={this.props.id}>
            <strong>{this.props.label}</strong>
            {this.displayRequiredOrOptional()}
          </FormLabel>
          <div>{this.showHelpLink()}</div>
        </Col>
        <Col md={this.determineInputColumnWidth()}>
          <FormControl
            as={this.props.as}
            rows={this.props.rows}
            data-index={this.props.index}
            id={this.props.id}
            data-testid={this.props.dataTestId}
            type={this.props.type ? this.props.type : "text"}
            name={this.props.name}
            onChange={(event) => {
              this.props.onChange(event.target.value);
            }}
            value={this.props.value}
            className={this.props.error ? "is-invalid" : ""}
          >
            {this.props.children}
          </FormControl>
          {this.props.note ? <p className="py-1">{this.props.note}</p> : null}
          {this.props.error ? <Error error={this.props.error} /> : null}
          <HelpBox showing={this.state.help_showing}>
            {this.props.helpContent}
          </HelpBox>
        </Col>
      </Row>
    );
  }
}

export default DesignInput;
