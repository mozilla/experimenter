import React from "react";
import { boundMethod } from "autobind-decorator";
import { Row, Col, Button } from "react-bootstrap";
import PrefBranch from "experimenter/components/PrefBranch";
export default class BranchManager extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      variants: {}
    };
  }
  componentDidMount() {
    let variants = this.props.values.variants;
    let variants_counter = variants.length;
    let variants_map = Object.assign({}, variants);
    let variant_keys = Object.keys(variants[0]);
    this.setState({
      variants: variants_map,
      variants_counter,
      variant_keys
    });
  }

  @boundMethod
  removeBranch(id) {
    delete this.state.variants[id];
    this.setState({ variants: this.state.variants });
  }

  @boundMethod
  addBranch() {
    this.state.variants[this.state.variants_counter++] = {};
    this.setState(this.state);
  }

  render() {
    return (
      <div>
        {Object.keys(this.state.variants).map((variant_id, index) => (
          <div>
            {React.cloneElement(this.props.branchComponent, {
              values: this.state.variants[variant_id],
              id: variant_id,
              type: this.props.values.type,
              index: index,
              remove: () => this.removeBranch(variant_id),
              errors: this.props.errors
            })}
          </div>
        ))}
        <Row>
          <Col className="text-right">
            <Button
              id="add-branch-button"
              variant="success"
              className="mb-4"
              onClick={this.addBranch}
            >
              <span className="fas fa-plus" /> Add Branch
            </Button>
          </Col>
        </Row>
      </div>
    );
  }
}
