(window.webpackJsonp=window.webpackJsonp||[]).push([[1,17],{2243:function(e,t,n){var r=n(2322),i=r.OWS_1_0_0,l=r.DCT,o=r.SMIL_2_0,a=r.SMIL_2_0_Language,_=r.GML_3_1_1,p=r.Filter_1_1_0,s=r.CSW_2_0_2,c=r.GML_3_2_0,m=r.GML_3_2_1,w=r.ISO19139_GCO_20070417,u=r.ISO19139_GMD_20070417,g=r.ISO19139_GMX_20070417,S=r.ISO19139_GSS_20070417,h=r.ISO19139_GTS_20070417,y=r.ISO19139_GSR_20070417,C=r.ISO19139_2_GMI_1_0,L=n(2561),E=n(2323).XLink_1_0,d=new(n(2324).Jsonix.Context)([i,L,l,E,o,a,_,p,s,c,m,w,u,g,S,h,y,C],{namespacePrefixes:{"http://www.opengis.net/cat/csw/2.0.2":"csw","http://www.opengis.net/ogc":"ogc","http://www.opengis.net/gml":"gml","http://purl.org/dc/elements/1.1/":"dc","http://purl.org/dc/terms/":"dct","http://www.isotc211.org/2005/gmd":"gmd","http://www.isotc211.org/2005/gco":"gco","http://www.isotc211.org/2005/gmi":"gmi","http://www.opengis.net/ows":"ows"}}),T=d.createMarshaller(),M=d.createUnmarshaller(),f={getRecords:function(e,t,n,r){var i={startPosition:e,maxRecords:t,abstractQuery:f.query("full",n&&f.constraint(n)),resultType:"results",service:"CSW",version:"2.0.2"};return r&&(i.outputSchema=r),i},getRecordById:function(e){return{TYPE_NAME:"CSW_2_0_2.GetRecordByIdType",elementSetName:{ObjectTYPE_NAME:"CSW_2_0_2.ElementSetNameType",value:"full"},id:Array.isArray(e)?e:[e],service:"CSW",version:"2.0.2"}},query:function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:"full",t=arguments.length>1?arguments[1]:void 0,n={"csw:Query":{TYPE_NAME:"CSW_2_0_2.QueryType",elementSetName:{TYPE_NAME:"CSW_2_0_2.ElementSetNameType",value:e},typeNames:[{key:"{http://www.opengis.net/cat/csw/2.0.2}Record",localPart:"Record",namespaceURI:"http://www.opengis.net/cat/csw/2.0.2",prefix:"csw",string:"{http://www.opengis.net/cat/csw/2.0.2}csw:Record"}]}};return t&&(n["csw:Query"].constraint=t),n},constraint:function(e){return{TYPE_NAME:"CSW_2_0_2.QueryConstraintType",version:"1.1.0",filter:e}}};e.exports={CSW:f,marshaller:T,unmarshaller:M}},2325:function(e,t,n){var r=n(2322),i=r.OWS_1_0_0,l=r.DC_1_1,o=r.DCT,a=r.SMIL_2_0,_=r.SMIL_2_0_Language,p=r.GML_3_1_1,s=r.Filter_1_1_0,c=r.CSW_2_0_2,m=n(2323).XLink_1_0,w=new(n(2324).Jsonix.Context)([i,l,o,m,a,_,p,s,c],{namespacePrefixes:{"http://www.opengis.net/cat/csw/2.0.2":"csw","http://www.opengis.net/ogc":"ogc","http://www.opengis.net/gml":"gml","http://www.opengis.net/ows":"ows"}}),u=w.createMarshaller(),g=w.createUnmarshaller();e.exports={Filter:{propertyName:function(e){return{PropertyName:e}},propertyIsLike:function(e,t){return{"ogc:PropertyIsLike":{TYPE_NAME:"Filter_1_1_0.PropertyIsLikeType",escapeChar:"\\\\",singleChar:"_",wildCard:"%",literal:{TYPE_NAME:"Filter_1_1_0.LiteralType",content:[t]},propertyName:{TYPE_NAME:"Filter_1_1_0.PropertyNameType",content:[e]}}}},bbox:function(e,t,n,r,i){return{"ows:BBOX":{TYPE_NAME:"Filter_1_1_0.BBOXType",envelope:{"gml:Envelope":{TYPE_NAME:"GML_3_1_1.EnvelopeType",lowerCorner:{TYPE_NAME:"GML_3_1_1.DirectPositionType",value:[e,t]},upperCorner:{TYPE_NAME:"GML_3_1_1.DirectPositionType",value:[n,r]},srsName:i}}}}},and:function(e){return{"ogc:And":{TYPE_NAME:"Filter_1_1_0.BinaryLogicOpType",ops:e}}},or:function(e){return{"ogc:Or":{TYPE_NAME:"Filter_1_1_0.BinaryLogicOpType",ops:e}}},filter:function(e,t){return{"ogc:Filter":{TYPE_NAME:"Filter_1_1_0.FilterType",logicOps:e,spatialOps:t}}}},marshaller:u,unmarshaller:g}},2561:function(e,t){e.exports={n:"DC_1_1",dens:"http://purl.org/dc/elements/1.1/",tis:[{ln:"ElementContainer",tn:"elementContainer",ps:[{n:"dcElement",mno:0,col:!0,mx:!1,dom:!1,en:"DC-element",ti:".SimpleLiteral",t:"er"},{n:"dcElement",mno:0,col:!0,mx:!1,dom:!1,en:"DC-element",ti:".URI",t:"er"}]},{ln:"SimpleLiteral",ps:[{n:"content",col:!0,dom:!1,t:"ers"},{n:"scheme",an:{lp:"scheme"},t:"a"}]},{ln:"URI",ti:"URI",sh:"DC-element",collection:!0,propertyInfos:[{type:"attribute",name:"name",attributeName:"name",typeInfo:"String"},{type:"attribute",name:"description",attributeName:"description",typeInfo:"String"},{type:"attribute",name:"protocol",attributeName:"protocol",typeInfo:"String"},{type:"value",name:"value",typeInfo:"String"}]}],eis:[{en:"identifier",ti:".SimpleLiteral",sh:"DC-element"},{en:"relation",ti:".SimpleLiteral",sh:"DC-element"},{en:"format",ti:".SimpleLiteral",sh:"DC-element"},{en:"title",ti:".SimpleLiteral",sh:"DC-element"},{en:"description",ti:".SimpleLiteral",sh:"DC-element"},{en:"source",ti:".SimpleLiteral",sh:"DC-element"},{en:"date",ti:".SimpleLiteral",sh:"DC-element"},{en:"type",ti:".SimpleLiteral",sh:"DC-element"},{en:"language",ti:".SimpleLiteral",sh:"DC-element"},{en:"DC-element",ti:".SimpleLiteral"},{en:"rights",ti:".SimpleLiteral",sh:"DC-element"},{en:"creator",ti:".SimpleLiteral",sh:"DC-element"},{en:"publisher",ti:".SimpleLiteral",sh:"DC-element"},{en:"contributor",ti:".SimpleLiteral",sh:"DC-element"},{en:"subject",ti:".SimpleLiteral",sh:"DC-element"},{en:"coverage",ti:".SimpleLiteral",sh:"DC-element"},{en:"URI",ti:".URI",sh:"DC-element"}]}}}]);