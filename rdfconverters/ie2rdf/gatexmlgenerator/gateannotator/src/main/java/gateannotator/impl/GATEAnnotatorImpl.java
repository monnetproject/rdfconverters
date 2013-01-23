package gateannotator.impl;
import gate.Annotation;
import gate.AnnotationSet;
import gate.Corpus;
import gate.CorpusController;
import gate.Document;
import gate.Factory;
import gate.Gate;
import gate.util.GateException;
import gate.util.persistence.PersistenceManager;
import gateannotator.GATEAnnotator;

import java.io.File;
import java.io.IOException;
import java.util.HashSet;
import java.util.Properties;
import java.util.Set;

public class GATEAnnotatorImpl implements GATEAnnotator {
	private CorpusController application;
	
	public GATEAnnotatorImpl() throws GateException, IOException {
		if (!Gate.isInitialised()) {
			Properties prop = new Properties();
			prop.load(GATEAnnotatorImpl.class.getClassLoader().getResourceAsStream("gateannotator.properties"));
			System.setProperty("gate.home", prop.getProperty("gateHome"));
			Gate.init();
		}
	}

	public void loadGappFile(File gappFile) throws IOException, GateException {
		this.application = (CorpusController) PersistenceManager.loadObjectFromFile(gappFile);
		Corpus corpus = Factory.newCorpus("BatchProcessApp Corpus");
		application.setCorpus(corpus);
	}
	
	@Override
	public String annotate(String text) throws GateException {
		// Show gate
		// MainFrame.getInstance().setVisible(true);
		
		Document doc = Factory.newDocument(text);

		//Run GATE process
		application.getCorpus().add(doc);
		application.execute();
		application.getCorpus().clear();

		//Get annotated XML output
		Set<Annotation> annotations = getAnnotations(doc, "Activity", "Company", "Customer", "Employee", "Location", "MonetaryValue");
		String docXMLString = doc.toXml(annotations, true);
		
		//Add the start and end offset of the annotation
		//Unfortunately .toXml() is implemented with StringBuilders, so
		//this must be done with string replacements rather than using an XML library.
		for (Annotation annotation : annotations) {
			Integer id = annotation.getId();
			Long start = annotation.getStartNode().getOffset();
			Long end = annotation.getEndNode().getOffset();
			//Ditch the "gate:" prefixing: no xmlns is outputted so it messes with parsers
			docXMLString = docXMLString.replaceAll("gate:gateId=\""+id+"\"", String.format("gateId=\"%d\" start=\"%d\" end=\"%d\"", id, start, end));
		}
		//Surround with a tag to make the XML valid enough to parse.
		docXMLString = "<?xml version=\"1.0\" ?><paragraph>" + docXMLString + "</paragraph>";
		
		
		
		
		Factory.deleteResource(doc);

		return docXMLString;
	}

	private Set<Annotation> getAnnotations(Document doc, String... annotationTypes) {
		Set<Annotation> annotations = new HashSet<Annotation>();
		for (String annotation : annotationTypes) {
			AnnotationSet annotsOfThisType = doc.getAnnotations().get((String) annotation);

			if (annotsOfThisType != null) {
				annotations.addAll(annotsOfThisType);
			}
		}
		return annotations;
	}
}
