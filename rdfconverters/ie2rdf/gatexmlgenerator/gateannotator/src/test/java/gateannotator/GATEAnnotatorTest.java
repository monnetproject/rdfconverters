package gateannotator;

import gate.util.GateException;
import gateannotator.impl.GATEAnnotatorImpl;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.util.Properties;

import org.apache.commons.io.FileUtils;
import org.junit.BeforeClass;
import org.junit.Test;

public class GATEAnnotatorTest {

	private static Properties properties;
	private static GATEAnnotatorImpl g;

	@BeforeClass
	public static void beforeClass() throws IOException, GateException {
		properties = new Properties();
		properties.load(properties.getClass().getResourceAsStream("/config.properties"));
		
		g = new GATEAnnotatorImpl();
		String filename = properties.getProperty("DaxXgapp");
		g.loadGappFile(new File(filename));
	}
	
	@Test
	public void test() throws IOException, GateException {
	    String text = FileUtils.readFileToString(
	    	//FileUtils.toFile(getClass().getResource("/DE000A1KRCK4__1361579223781.txt"))
            FileUtils.toFile(this.getClass().getResource("/DE000A1KRCK4__1361579223781.txt"))
        );
		System.out.println(g.annotate(text));
	}

}
