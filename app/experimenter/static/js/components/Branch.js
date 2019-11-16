import { boundClass } from "autobind-decorator";
import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Button, Row, Col } from "react-bootstrap";

@boundClass
class Branch extends React.PureComponent {
  static propTypes = {
    branch: PropTypes.instanceOf(Map),
    branchFieldsComponent: PropTypes.func,
    errors: PropTypes.instanceOf(Map),
    index: PropTypes.number,
    onChange: PropTypes.func,
    remove: PropTypes.func,
  };

  handleChange(key, value) {
    const { onChange, branch } = this.props;
    const updated = branch
      .set("is_control", this.props.index === 0)
      .set(key, value);
    onChange(updated);
  }

  renderTitle() {
    if (this.props.index === 0) {
      return <h4>Control Branch</h4>;
    }
    return <h4>Branch {this.props.index}</h4>;
  }

  renderRemoveButton() {
    if (this.props.index === 0) {
      return null;
    }
    return (
      <Button
        variant="danger"
        onClick={() => {
          this.props.remove(this.props.index);
        }}
        id="remove-branch-button"
      >
        <span className="fas fa-times" /> Remove Branch
      </Button>
    );
  }

  render() {
    const BranchFields = this.props.branchFieldsComponent;

    return (
      <div key={this.props.index} id="control-branch-group">
        <Row className="mb-3">
          <Col md={{ span: 4, offset: 3 }}>{this.renderTitle()}</Col>
          <Col md={5} className="text-right">
            {this.renderRemoveButton()}
          </Col>
        </Row>

        <BranchFields
          handleChange={this.handleChange}
          index={this.props.index}
          branch={this.props.branch}
          errors={this.props.errors}
        />

        <hr className="heavy-line my-5" />
      </div>
    );
  }
}

export default Branch;
