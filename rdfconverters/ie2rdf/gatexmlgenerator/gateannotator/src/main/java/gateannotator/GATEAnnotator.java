package gateannotator;
import gate.util.GateException;

import java.io.File;
import java.io.IOException;


public interface GATEAnnotator {
	/**
	 * Load the supplied gapp file into the GATE instance.
	 * @throws IOException For file read errors
	 * @throws GateException For GATE annotation errors
	 */
	public void loadGappFile(File gappFile) throws IOException, GateException;
	/**
	 * Process text in gate and return the output (text with inline XML annotations) 
	 * as a String
	 * @throws GateException For GATE annotation errors
	 */
	public String annotate(String text) throws GateException;
}
