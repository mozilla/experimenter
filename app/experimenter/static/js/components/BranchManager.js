import React from "react";
import { Row, Col, Button } from "react-bootstrap";
import {boundClass} from "autobind-decorator";

@boundClass
class BranchManager extends React.Component {
  constructor(props){
    super(props);
    this.state={
      variants:props.variants,
    };
  }
  handleChange(index, value){
    const variants = [...this.props.variants];
    variants.splice(index,1, value);
    this.setState({variants});
    this.props.onChange(variants);

  }

  componentDidMount(){
    this.props.onChange(this.state.variants);
  }

  render() {
    const {onAddBranch, onRemoveBranch} = this.props;
    const BranchComponent = this.props.branchComponent;
    return (
      <div>
        {this.props.variants.map((variant, index) => (
          <div>
            <BranchComponent
              values={variant}
              id={index}
              type={this.props.type}
              index={index}
              remove={onRemoveBranch}
              errors={this.props.errors}
              onChange={(value)=>{this.handleChange(index, value)}}
            />
          </div>
        ))}
        <Row>
          <Col className="text-right">
            <Button
              id="add-branch-button"
              variant="success"
              className="mb-4"
              onClick={onAddBranch}
            >
              <span className="fas fa-plus" /> Add Branch
            </Button>
          </Col>
        </Row>
      </div>
    );
  }
}
export default BranchManager;
