import React from "react";
import DesignInput from "experimenter/components/DesignInput";
import BranchManager from "experimenter/components/BranchManager";
import GenericBranch from "experimenter/components/GenericBranch";

class GenericForm extends React.Component {
  render(){
    return (
      <div>
        <DesignInput
          label="Design"
          name="design"
          handleInputChange={this.props.handleInputChange}
          value={this.props.values.design}
          error={this.props.errors ? this.props.errors.design : ""}
          as="textarea"
          rows="10"
          helpContent={
            <div>
              <p>Specify the design of the experiment.</p>
            </div>
          }
        />
        <hr className="heavy-line my-5" />
        <BranchManager
          variants={this.props.values.variants} 
          onAddBranch={this.props.onAddBranch}
          onRemoveBranch={this.props.onRemoveBranch}
          onChange={(value)=>{this.props.handleDataChange("variants", value)}}
          type="generic" 
          branchComponent={GenericBranch}
          errors={this.props.errors} 
        />
      </div>
    );
  }
}

export default GenericForm;
