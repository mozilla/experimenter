import React from "react";
import { Button, Row, Col, FormControl } from "react-bootstrap";
import DesignInput from "experimenter/components/DesignInput";
import {boundClass} from "autobind-decorator";

@boundClass
class GenericBranch extends React.Component {

  constructor(props){
    super(props);
    const {values} = props;
    this.state = {
      ratio: values.ratio,
      name : values.name,
      description: values.description,
      is_control: props.index === 0,
      id : values.id
    }
  }
  handleChange(key, value){
    const state = {
      ...this.state,
      [key]: value
    };
    this.setState(state);
    this.props.onChange(state);
  }

  componentDidMount(){
    this.props.onChange(this.state);
  }

  render(){
    return (
      <div key={this.props.id}>
        <Row className="mb-3">
          <Col md={{ span: 4, offset: 3 }}>
            {this.props.values.is_control ? (
              <h4>Control Branch</h4>
            ) : (
              <h4>Branch {this.props.id}</h4>
            )}
          </Col>
          <Col md={5} className="text-right">
            {this.props.id != 0 ? (
              <Button
                variant="danger"
                onClick={()=>this.props.remove(this.props.index)}
                id="remove-branch-button"
              >
                <span className="fas fa-times"></span> Remove Branch
              </Button>
            ) : null}
          </Col>
        </Row>
        <DesignInput
          label="Branch Size"
          name={"variants[" + this.props.id + "][ratio]"}
          id={"variants-" + this.props.id + "-ratio"}
          value={this.props.values.ratio}
          onChange={(value)=>{this.handleChange("ratio",value)}}
          error={
            this.props.errors.variants ? this.props.errors.variants[this.props.index].ratio : ""
          }
          helpContent={
            <div>
              <p>
                Choose the size of this branch represented as a whole number. The
                size of all branches together must be equal to 100. It does not
                have to be exact, so these sizes are simply a recommendation of
                the relative distribution of the branches.
              </p>
              <p>
                <strong>Example:</strong> 50
              </p>
            </div>
          }
        />
        <DesignInput
          label="Name"
          name={"variants[" + this.props.id + "][name]"}
          id={"variants-" + this.props.id + "-name"}
          value={this.props.values.name}
          onChange={(value)=>{this.handleChange("name",value)}}
          error={
            this.props.errors.variants ? this.props.errors.variants[this.props.index].name : ""
          }
          helpContent={
            <div>
              <p>
                The control group should represent the users receiving the
                existing, unchanged version of what you're testing. For example,
                if you're testing making a button larger to see if users click on
                it more often, the control group would receive the existing button
                size. You should name your control branch based on the experience
                or functionality that group of users will be receiving. Don't name
                it 'Control Group', we already know it's the control group!
              </p>
              <p>
                <strong>Example:</strong> Normal Button Size
              </p>
            </div>
          }
        />
        <DesignInput
          label="Description"
          name={"variants[" + this.props.id + "][description]"}
          id={"variants-" + this.props.id + "-description"}
          as="textarea"
          rows="3"
          value={this.props.values.description}
          onChange={(value)=>{this.handleChange("description", value)}}
          error={
            this.props.errors.variants
              ? this.props.errors.variants[this.props.index].description
              : ""
          }
          helpContent={
            <div>
              <p>
                Describe the experience or functionality the control group will
                receive in more detail.
              </p>
              <p>
                <strong>Example:</strong> The control group will receive the
                existing 80px sign in button located at the top right of the
                screen.
              </p>
            </div>
          }
        />
        <hr className="heavy-line my-5" />
      </div>
    );
  }
}
export default GenericBranch;