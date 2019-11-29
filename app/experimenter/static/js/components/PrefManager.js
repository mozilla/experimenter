import { boundClass } from "autobind-decorator";
import { fromJS, List, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col, Button } from "react-bootstrap";

import Pref from "experimenter/components/Pref";

@boundClass
class PrefManager extends React.PureComponent {
  static propTypes = {
    preferences: PropTypes.instanceOf(List),
    errors: PropTypes.instanceOf(List),
    onErrorChange: PropTypes.func,
    onDataChange: PropTypes.func,
  };

  handlePrefChange(index, value) {
    const { preferences, onDataChange } = this.props;

    onDataChange(preferences.set(index, value));
  }

  addPref() {
    const { preferences, errors, onDataChange, onErrorChange } = this.props;
    onDataChange(preferences.push(fromJS({})));
    onErrorChange(errors.push(fromJS({})));
  }

  removePref(index) {
    const { preferences, errors, onDataChange, onErrorChange } = this.props;

    onDataChange(preferences.delete(index));
    onErrorChange(errors.delete(index));
  }

  renderPref(preference, index) {
    const { errors } = this.props;

    return (
      <Col md={{ span: 9, offset: 2 }}>
        <Pref
          key={index}
          index={index}
          preference={preference}
          errors={errors.get(index, new Map())}
          remove={this.removePref}
          onChange={value => this.handlePrefChange(index, value)}
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
