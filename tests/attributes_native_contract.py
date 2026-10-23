#!/usr/bin/env python3
"""Compile actual Swift bridge methods with recording dependency declarations.
Host boundary regression; no mobile app/backend execution.
"""
from pathlib import Path
import subprocess,tempfile,json,sys
root=Path(__file__).resolve().parents[1]
def method(s,needle):
 start=s.index(needle);op=s.index('{',start);depth=1;i=op+1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[start:i]
source=(root/'src/ios/PurchasesPlugin+Attribution.swift').read_text()
body='\n'.join(method(source,n) for n in ['func setAttributes(','func setSubscriberAttribute('])
code="""import Foundation
class CDVInvokedUrlCommand {let arguments:[Any];init(_ x:Any){arguments=[x]}}
class CommonFunctionality {static var received:[String:Any]?;static func setAttributes(_ x:[String:Any]){received=x}}
class Plugin {var bad=0
func sendBadParameterFor(command:CDVInvokedUrlCommand,parameterNamed:String,expectedType:Any.Type){bad+=1}
func sendOKFor(command:CDVInvokedUrlCommand){}
"""+body+"""
}
let p=Plugin();var scalar:String?;var rows:[String:Bool]=[:]
p.setSubscriberAttribute(command:CDVInvokedUrlCommand(NSNull()),name:"displayName",setFunction:{scalar=$0})
rows["nullScalarDeletes"] = scalar == ""
p.setAttributes(command:CDVInvokedUrlCommand(["deleted":NSNull(),"kept":"updated"] as [String:Any]))
rows["nullMapEntryForwarded"] = CommonFunctionality.received?["deleted"] is NSNull
rows["siblingUpdatePreserved"] = CommonFunctionality.received?["kept"] as? String == "updated"
rows["validNullInputsAccepted"] = p.bad == 0
p.setSubscriberAttribute(command:CDVInvokedUrlCommand("value"),name:"displayName",setFunction:{scalar=$0})
rows["stringControlForwarded"] = scalar == "value"
p.setAttributes(command:CDVInvokedUrlCommand(["deleted":"","kept":"updated"]))
rows["emptyStringMapControl"] = CommonFunctionality.received?["deleted"] as? String == ""
p.setSubscriberAttribute(command:CDVInvokedUrlCommand(42),name:"displayName",setFunction:{scalar=$0})
p.setAttributes(command:CDVInvokedUrlCommand(["invalid":42]))
rows["invalidInputsRejected"] = p.bad >= 2
print(String(data:try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]),encoding:.utf8)!)
"""
with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp);(path/'test.swift').write_text(code)
 subprocess.run(['xcrun','swiftc',str(path/'test.swift'),'-o',str(path/'test')],check=True)
 rows=json.loads(subprocess.check_output([str(path/'test')],text=True))
 print(json.dumps(rows,indent=2));print(f"{sum(rows.values())} passed / {sum(not v for v in rows.values())} failed")
 sys.exit(0 if all(rows.values()) else 1)
