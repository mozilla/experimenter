import { boundClass } from "autobind-decorator";
import Pref from "experimenter/components/Pref";
import { fromJS, List, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Button, Col, Row } from "react-bootstrap";

@boundClass
class PrefManager extends React.PureComponent {
  static propTypes = {
    preferences: PropTypes.instanceOf(List),
    errors: PropTypes.instanceOf(List),
    onErrorChange: PropTypes.func,
    onDataChange: PropTypes.func,
    variantIndex: PropTypes.number,
    rolloutType: PropTypes.string,
  };

  handlePrefChange(index, value) {
    const { preferences, onDataChange } = this.props;

    onDataChange(preferences.set(index, value));
  }

  addPref() {
    const { preferences, errors, onDataChange, onErrorChange } = this.props;
    onDataChange(preferences.push(fromJS({ pref_value: "" })));
    onErrorChange(errors.push(fromJS({})));
  }

  removePref(index) {
    const { preferences, errors, onDataChange, onErrorChange } = this.props;

    onDataChange(preferences.delete(index));
    onErrorChange(errors.delete(index));
  }

  renderPref(preference, index) {
    const { errors, preferences } = this.props;

    return (
      <Col md={{ span: 11, offset: 1 }}>
        <Pref
          key={`${index}${preferences.size}`}
          index={index}
          numOfPreferences={preferences.size}
          preference={preference}
          errors={errors.get(index, new Map())}
          remove={this.removePref}
          onChange={(value) => this.handlePrefChange(index, value)}
          variantIndex={this.props.variantIndex}
          rolloutType={this.props.rolloutType}
        />
      </Col>
    );
  }

  render() {
    const { preferences } = this.props;
    return (
      <React.Fragment>
        {preferences.map((p, i) => this.renderPref(p, i))}
        <Row>
          <Col className="text-right">
            <Button
              id="add-pref-button"
              variant="outline-success"
              className="mb-4"
              onClick={this.addPref}
            >
              <span className="fas fa-plus" /> Add Pref
            </Button>
          </Col>
        </Row>
      </React.Fragment>
    );
  }
}
export default PrefManager;
