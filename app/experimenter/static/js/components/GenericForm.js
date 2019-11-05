import React from "react";
import DesignInput from "experimenter/components/DesignInput";
import BranchManager from "experimenter/components/BranchManager";
import GenericBranch from "experimenter/components/GenericBranch";

export default function GenericForm(props) {
  return (
    <div>
      <DesignInput
        label="Design"
        name="design"
        handleInputChange={props.handleInputChange}
        value={props.values.design}
        error={props.errors ? props.errors.design : ""}
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
        variants={props.values.variants} 
        onAddBranch={props.onAddBranch}
        onRemoveBranch={props.onRemoveBranch} 
        type="generic" 
        branchComponent={GenericBranch}
        errors={props.errors} 
      />
    </div>
  );
}
