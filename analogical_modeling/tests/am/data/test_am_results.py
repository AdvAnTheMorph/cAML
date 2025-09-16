"""weka.classifiers.lazy.AM.data"""

import unittest

from analogical_modeling.analogical_modeling import AnalogicalModeling
from analogical_modeling.tests.am import test_utils


class AMResultsTest(unittest.TestCase):
    """Test the data contained in AMResults after classifying the chapter 3 data."""
    def setUp(self):
        self.train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        self.test = self.train[0]
        self.train.data.drop(index=0, inplace=True)

        self.am = AnalogicalModeling()
        self.am.build_classifier(self.train)
        self.am.distribution_for_instance(self.test)

        self.as_quadratic = self.am.get_results()
        self.am.set_linear_count(True)
        self.am.distribution_for_instance(self.test)
        self.as_linear = self.am.get_results()

    def test_exemplar_quadratic_effects(self):
        effects = {str(k): v for k, v in self.as_quadratic.get_exemplar_effect_map().items()}
        self.assertEqual(4, len(effects))
        # TODO
#
# 	@Test
# 	public void exemplarQuadraticEffectsTest() {
# 		Map<String, BigDecimal> effects = instanceKeysToString(asQuadratic.getExemplarEffectMap());
# 		assertEquals(effects.size(), 4);
# 		assertThat(effects, hasEntry(equalTo("3,1,0,e"), closeTo(new BigDecimal("0.3076923"), EPSILON)));
# 		assertThat(effects, hasEntry(equalTo("0,3,2,r"), closeTo(new BigDecimal("0.1538462"), EPSILON)));
# 		assertThat(effects, hasEntry(equalTo("2,1,2,r"), closeTo(new BigDecimal("0.2307692"), EPSILON)));
# 		assertThat(effects, hasEntry(equalTo("3,1,1,r"), closeTo(new BigDecimal("0.3076923"), EPSILON)));
# 	}
#
# 	@Test
# 	public void exemplarLinearEffectsTest() {
# 		Map<String, BigDecimal> effects = instanceKeysToString(asLinear.getExemplarEffectMap());
# 		assertEquals(effects.size(), 4);
# 		assertThat(effects, hasEntry(equalTo("3,1,0,e"), closeTo(new BigDecimal("0.2857143"), EPSILON)));
# 		assertThat(effects, hasEntry(equalTo("0,3,2,r"), closeTo(new BigDecimal("0.1428571"), EPSILON)));
# 		assertThat(effects, hasEntry(equalTo("2,1,2,r"), closeTo(new BigDecimal("0.2857143"), EPSILON)));
# 		assertThat(effects, hasEntry(equalTo("3,1,1,r"), closeTo(new BigDecimal("0.2857143"), EPSILON)));
# 	}
#
# 	@Test
# 	public void quadraticPointersTest() {
# 		assertEquals(asQuadratic.getTotalPointers(), BigInteger.valueOf(13));
# 		assertEquals(asQuadratic.getClassPointers(), new HashMap<String, BigInteger>() {
# 			{
# 				put("r", BigInteger.valueOf(9));
# 				put("e", BigInteger.valueOf(4));
# 			}
# 		});
# 		Map<String, BigInteger> pointers = instanceKeysToString(asQuadratic.getExemplarPointers());
# 		assertEquals(pointers.size(), 4);
# 		assertThat(pointers, hasEntry("3,1,0,e", BigInteger.valueOf(4)));
# 		assertThat(pointers, hasEntry("0,3,2,r", BigInteger.valueOf(2)));
# 		assertThat(pointers, hasEntry("2,1,2,r", BigInteger.valueOf(3)));
# 		assertThat(pointers, hasEntry("3,1,1,r", BigInteger.valueOf(4)));
# 	}
#
# 	@Test
# 	public void linearPointersTest() {
# 		assertEquals(asLinear.getTotalPointers(), BigInteger.valueOf(7));
# 		assertEquals(asLinear.getClassPointers(), new HashMap<String, BigInteger>() {
# 			{
# 				put("r", BigInteger.valueOf(5));
# 				put("e", BigInteger.valueOf(2));
# 			}
# 		});
# 		Map<String, BigInteger> pointers = instanceKeysToString(asLinear.getExemplarPointers());
# 		assertEquals(pointers.size(), 4);
# 		assertThat(pointers, hasEntry("3,1,0,e", BigInteger.valueOf(2)));
# 		assertThat(pointers, hasEntry("0,3,2,r", BigInteger.valueOf(1)));
# 		assertThat(pointers, hasEntry("2,1,2,r", BigInteger.valueOf(2)));
# 		assertThat(pointers, hasEntry("3,1,1,r", BigInteger.valueOf(2)));
# 	}
#
# 	@Test
# 	public void quadraticClassDistributionTest() {
# 		Map<String, BigDecimal> distribution = asQuadratic.getClassLikelihood();
#
# 		assertEquals(distribution.size(), 2);
# 		// test to 10 decimal places, the number used by AMUtils.mathContext
# 		assertThat(distribution.get("r"), closeTo(new BigDecimal("0.6923077"), EPSILON));
# 		assertThat(distribution.get("e"), closeTo(new BigDecimal("0.3076923"), EPSILON));
#
# 		assertEquals(asQuadratic.getPredictedClasses(), new HashSet<String>() {
# 			{
# 				add("r");
# 			}
# 		});
# 		assertThat(asQuadratic.getClassProbability(), closeTo(new BigDecimal("0.6923077"), EPSILON));
# 	}
#
# 	@Test
# 	public void linearClassDistributionTest() {
# 		Map<String, BigDecimal> distribution = asLinear.getClassLikelihood();
#
# 		assertEquals(distribution.size(), 2);
# 		// test to 10 decimal places, the number used by AMUtils.mathContext
# 		assertThat(distribution.get("r"), closeTo(new BigDecimal("0.7142857"), EPSILON));
# 		assertThat(distribution.get("e"), closeTo(new BigDecimal("0.2857143"), EPSILON));
#
# 		assertEquals(asLinear.getPredictedClasses(), new HashSet<String>() {
# 			{
# 				add("r");
# 			}
# 		});
# 		assertThat(asLinear.getClassProbability(), closeTo(new BigDecimal("0.7142857"), EPSILON));
# 	}
#
#     @Test
#     public void classifiedExTest() {
#         assertEquals(asQuadratic.getClassifiedEx(), test);
#     }
#     // TODO: test with linear counting
#     // TODO: test toString
#
# 	private static <T> Map<String, T> instanceKeysToString(Map<Instance, T> instanceMap) {
# 		Map<String, T> translated = new HashMap<>();
# 		for(Entry<Instance, T> e : instanceMap.entrySet()) {
# 			translated.put(e.getKey().toString(), e.getValue());
# 		}
# 		return translated;
# 	}
#
# 	@Test
# 	public void getGangEffectsTest() {
# 		List<GangEffect> effects = asQuadratic.getGangEffects();
# 		assertEquals("Should return 3 gang effects ordered by number of pointers",
# 				List.of("3 1 *", "* 1 2", "* * 2"),
# 				effects.stream().map(e -> e.getSubcontext().getDisplayLabel()).collect(toList()));
# 	}
# }
