"""weka.classifiers.lazy.AM.label"""

import unittest

from analogical_modeling.am.label.missing_data_compare import \
    MissingDataCompare


# import org.junit.BeforeClass;
# import org.junit.Test;
#
# import weka.core.Attribute;
# import weka.core.DenseInstance;
# import weka.core.Instance;
# import weka.core.Instances;
#
# import java.util.ArrayList;
#
# import static org.junit.Assert.assertFalse;
# import static org.junit.Assert.assertTrue;

class TestMissingDataCompare(unittest.TestCase):
    # def setUpClass(self):
    #     self.atts = []
    #     att = Attribute("a")
    #     atts.append(att)
    #
    #     dataset = Instances("TestInstance", atts, 0)
    #     dataset.set_class_index(dataset.num_attributes() -1)

    def test_match(self):
        mdc = MissingDataCompare.MATCH
        assert mdc.matches("a", "a", "a")


# public class MissingDataCompareTest {
#     private static ArrayList<Instance> instances;
#     private static Attribute att;
#
#     @BeforeClass
#     public static void setupBeforeClass() {
#         ArrayList<Attribute> atts = new ArrayList<>();
#         att = new Attribute("a");
#         atts.add(att);
#
#         Instances dataset = new Instances("TestInstances", atts, 0);
#         dataset.setClassIndex(dataset.numAttributes() - 1);
#
#         double[][] data = new double[][]{
#             new double[]{Double.NaN}, new double[]{0}
#         };
#         instances = new ArrayList<>();
#         for (double[] datum : data) {
#             Instance instance = new DenseInstance(6, datum);
#             instance.setDataset(dataset);
#             instances.add(instance);
#         }
#     }
#
#     @Test
#     public void testMatch() {
#         MissingDataCompare mc = MissingDataCompare.MATCH;
#         assertTrue(mc.matches(instances.get(0), instances.get(0), att));
#         assertTrue(mc.matches(instances.get(0), instances.get(1), att));
#         assertTrue(mc.matches(instances.get(1), instances.get(0), att));
#     }
#
#     @Test
#     public void testMismatch() {
#         MissingDataCompare mc = MissingDataCompare.MISMATCH;
#         assertFalse(mc.matches(instances.get(0), instances.get(0), att));
#         assertFalse(mc.matches(instances.get(0), instances.get(1), att));
#         assertFalse(mc.matches(instances.get(1), instances.get(0), att));
#     }
#
#     @Test
#     public void testVariable() {
#         MissingDataCompare mc = MissingDataCompare.VARIABLE;
#         assertTrue(mc.matches(instances.get(0), instances.get(0), att));
#         assertFalse(mc.matches(instances.get(0), instances.get(1), att));
#         assertFalse(mc.matches(instances.get(1), instances.get(0), att));
#     }
#
# }
