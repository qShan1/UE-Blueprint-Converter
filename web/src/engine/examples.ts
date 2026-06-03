/**
 * Embedded example blueprints for offline use.
 */

export interface ExampleInfo {
  name: string
  label: string
  content: string
}

const simpleEvent = `Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
    NodePosX=256
    NodePosY=128
    NodeGuid=ABCDEF0123456789
    CustomFunctionName="EventBeginPlay"
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_2"
            PinName="then"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="self"
        PinDirection=EGPD_Output
        PinType.PinCategory="object"
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_CallFunction Name="K2Node_CallFunction_0"
    NodePosX=512
    NodePosY=128
    NodeGuid=ABCDEF0123456790
    FunctionReference="/Script/Engine.KismetSystemLibrary.PrintString"
    bIsPureCast=False
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="self"
        PinDirection=EGPD_Input
        PinType.PinCategory="object"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="InString"
        PinDirection=EGPD_Input
        PinType.PinCategory="string"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_2"
        PinName="then"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_3"
            PinName="then"
            PinDirection=EGPD_Output
            PinType.PinCategory="exec"
        End Object)
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_3"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
End Object`

const branchFlow = `Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
    NodePosX=256
    NodePosY=128
    NodeGuid=BRANCH_EVENT_01
    CustomFunctionName="EventBeginPlay"
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_branch_input"
            PinName="exec_in"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_IfThenElse Name="K2Node_IfThenElse_0"
    NodePosX=480
    NodePosY=128
    NodeGuid=BRANCH_NODE_02
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="exec_in"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="Condition"
        PinDirection=EGPD_Input
        PinType.PinCategory="boolean"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_2"
        PinName="true"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_print_input"
            PinName="exec_in"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_3"
        PinName="false"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_delay_input"
            PinName="exec_in"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_CallFunction Name="K2Node_CallFunction_1"
    NodePosX=704
    NodePosY=64
    NodeGuid=BRANCH_PRINT_03
    FunctionReference="/Script/Engine.KismetSystemLibrary.PrintString"
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="exec_in"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="InString"
        PinDirection=EGPD_Input
        PinType.PinCategory="string"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_2"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_CallFunction Name="K2Node_CallFunction_2"
    NodePosX=704
    NodePosY=256
    NodeGuid=BRANCH_DELAY_04
    FunctionReference="/Script/Engine.KismetSystemLibrary.Delay"
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="exec_in"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="Duration"
        PinDirection=EGPD_Input
        PinType.PinCategory="float"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_2"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
End Object`

const variableAndLoop = `Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
    NodePosX=256
    NodePosY=128
    NodeGuid=LOOP_EVENT_01
    CustomFunctionName="EventBeginPlay"
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_loop_input"
            PinName="exec_in"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_VariableGet Name="K2Node_VariableGet_0"
    NodePosX=440
    NodePosY=128
    NodeGuid=LOOP_VAR_GET_02
    VariableName="Counter"
    VariableType="int"
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="Counter"
        PinDirection=EGPD_Output
        PinType.PinCategory="int"
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_ForLoop Name="K2Node_ForLoop_0"
    NodePosX=480
    NodePosY=128
    NodeGuid=LOOP_NODE_03
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="exec_in"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="LoopBody"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_var_set_input"
            PinName="exec_in"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_2"
        PinName="Completed"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_3"
        PinName="FirstIndex"
        PinDirection=EGPD_Input
        PinType.PinCategory="int"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_4"
        PinName="LastIndex"
        PinDirection=EGPD_Input
        PinType.PinCategory="int"
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_VariableSet Name="K2Node_VariableSet_1"
    NodePosX=704
    NodePosY=128
    NodeGuid=LOOP_VAR_SET_04
    VariableName="Counter"
    VariableType="int"
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="exec_in"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="Counter"
        PinDirection=EGPD_Input
        PinType.PinCategory="int"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_2"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
End Object`

export const EMBEDDED_EXAMPLES: ExampleInfo[] = [
  { name: 'simple_event', label: 'Simple Event', content: simpleEvent },
  { name: 'branch_flow', label: 'Branch Flow', content: branchFlow },
  { name: 'variable_and_loop', label: 'Variable & Loop', content: variableAndLoop },
]