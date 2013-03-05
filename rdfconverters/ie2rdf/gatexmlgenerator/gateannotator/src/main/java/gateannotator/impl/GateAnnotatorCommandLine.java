package gateannotator.impl;

import gateannotator.GATEAnnotator;
import java.io.File;
import java.util.Iterator;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;

public class GateAnnotatorCommandLine {
	private static void usage() {
		System.out.println("GateAnnotatorCommandLine gappFile sourcedir destinationdir");
	}

	public static void main(String[] args) throws Exception {
		// It is better to batch convert because Gate.init() takes a few seconds
		// to run.
		// Yes, this process is tied together with string.

		if (args.length <= 2) {
			usage();
			return;
		}

		String gappFile = args[0];
		System.out.println(args[0]);
		System.out.println(args[1]);
		System.out.println(args[2]);
		GATEAnnotator batchProcessApp = new GATEAnnotatorImpl();
		batchProcessApp.loadGappFile(new File(gappFile));

		File inputDir = new File(args[1]);
		int pathLength = inputDir.getAbsolutePath().length();
		@SuppressWarnings("unchecked")
		Iterator<File> files = FileUtils.iterateFiles(inputDir, null, true);
		while (files.hasNext()) {
			try {
				File file = files.next();

				String dirDiff = FilenameUtils.getFullPath(file.getAbsolutePath()).substring(pathLength);

				File outDir = new File(args[2] + File.separator + dirDiff);
				outDir.mkdirs();
				File outFile = new File(outDir + File.separator + FilenameUtils.getBaseName(file.getAbsolutePath())
						+ ".xml");
				System.out.println("Processing " + file.getName() + " -> " + outFile);

				String text = FileUtils.readFileToString(file);
				String xml = batchProcessApp.annotate(text);
				FileUtils.writeStringToFile(outFile, xml);
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
	}
}
