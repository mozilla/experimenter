import { boundClass } from "autobind-decorator";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col, FormLabel } from "react-bootstrap";
import Select from "react-select";

import Error from "experimenter/components/Error";
import HelpBox from "experimenter/components/HelpBox";

@boundClass
class LabeledMultiSelect extends React.PureComponent {
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
    options: PropTypes.array,
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

  render() {
    return (
      <Row className="mb-3">
        <Col md={this.props.labelColumnWidth} className="text-right">
          <FormLabel for={this.props.id}>
            <strong>{this.props.label}</strong>
            {this.displayRequiredOrOptional()}
          </FormLabel>
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
        </Col>
        <Col md={this.determineInputColumnWidth()}>
          <Select
            isMulti
            options={this.props.options}
            id={this.props.id}
            name={this.props.name}
            value={this.props.value}
            className={this.props.error ? "is-invalid" : ""}
            onChange={selection => {
              this.props.onChange(selection, this.props.name);
            }}
          />
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

export default LabeledMultiSelect;
