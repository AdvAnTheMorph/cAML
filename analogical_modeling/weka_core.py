# /*
#  *   This program is free software: you can redistribute it and/or modify
#  *   it under the terms of the GNU General Public License as published by
#  *   the Free Software Foundation, either version 3 of the License, or
#  *   (at your option) any later version.
#  *
#  *   This program is distributed in the hope that it will be useful,
#  *   but WITHOUT ANY WARRANTY; without even the implied warranty of
#  *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  *   GNU General Public License for more details.
#  *
#  *   You should have received a copy of the GNU General Public License
#  *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  */
#
# /*
#  *    Instances.java
#  *    Copyright (C) 1999-2012 University of Waikato, Hamilton, New Zealand
#  *
#  */
#
# package weka.core;
#
# import java.io.FileReader;
# import java.io.IOException;
# import java.io.Reader;
# import java.io.Serializable;
# import java.util.AbstractList;
# import java.util.ArrayList;
# import java.util.Enumeration;
# import java.util.HashMap;
# import java.util.HashSet;
# import java.util.List;
# import java.util.Map.Entry;
# import java.util.Random;
#
# import weka.core.converters.ArffLoader.ArffReader;
# import weka.core.converters.ConverterUtils.DataSource;
#
# /**
#  * Class for handling an ordered set of weighted instances.
#  * <p>
#  *
#  * Typical usage:
#  * <p>
#  *
#  * <pre>
#  * import weka.core.converters.ConverterUtils.DataSource;
#  * ...
#  *
#  * // Read all the instances in the file (ARFF, CSV, XRFF, ...)
#  * DataSource source = new DataSource(filename);
#  * Instances instances = source.getDataSet();
#  *
#  * // Make the last attribute be the class
#  * instances.setClassIndex(instances.numAttributes() - 1);
#  *
#  * // Print header and instances.
#  * System.out.println("\nDataset:\n");
#  * System.out.println(instances);
#  *
#  * ...
#  * </pre>
#  * <p>
#  *
#  * All methods that change a set of instances are safe, ie. a change of a set of
#  * instances does not affect any other sets of instances. All methods that
#  * change a datasets's attribute information clone the dataset before it is
#  * changed.
#  *
#  * @author Eibe Frank (eibe@cs.waikato.ac.nz)
#  * @author Len Trigg (trigg@cs.waikato.ac.nz)
#  * @author FracPete (fracpete at waikato dot ac dot nz)
#  * @version $Revision: 15569 $
#  */
# public class Instances extends AbstractList<Instance> implements Serializable,
# RevisionHandler {
#
#   /** for serialization */
#   static final long serialVersionUID = -19412345060742748L;
#
#   /** The filename extension that should be used for arff files */
#   public final static String FILE_EXTENSION = ".arff";
#
#   /**
#    * The filename extension that should be used for bin. serialized instances
#    * files
#    */
#   public final static String SERIALIZED_OBJ_FILE_EXTENSION = ".bsi";
#
#   /** The keyword used to denote the start of an arff header */
#   public final static String ARFF_RELATION = "@relation";
#
#   /** The keyword used to denote the start of the arff data section */
#   public final static String ARFF_DATA = "@data";
#
#   /** The dataset's name. */
#   protected/* @spec_public non_null@ */String m_RelationName;
#
#   /** The attribute information. */
#   protected/* @spec_public non_null@ */ArrayList<Attribute> m_Attributes;
#   /*
#    * public invariant (\forall int i; 0 <= i && i < m_Attributes.size();
#    * m_Attributes.get(i) != null);
#    */
#
#   /** A map to quickly find attribute indices based on their names. */
#   protected HashMap<String, Integer> m_NamesToAttributeIndices;
#
#   /** The instances. */
#   protected/* @spec_public non_null@ */ArrayList<Instance> m_Instances;
#
#   /** The class attribute's index */
#   protected int m_ClassIndex;
#   // @ protected invariant classIndex() == m_ClassIndex;
#
#   /**
#    * The lines read so far in case of incremental loading. Since the
#    * StreamTokenizer will be re-initialized with every instance that is read, we
#    * have to keep track of the number of lines read so far.
#    *
#    * @see #readInstance(Reader)
#    */
#   protected int m_Lines = 0;
#
#   /**
#    * Reads an ARFF file from a reader, and assigns a weight of one to each
#    * instance. Lets the index of the class attribute be undefined (negative).
#    *
#    * @param reader the reader
#    * @throws IOException if the ARFF file is not read successfully
#    */
#   public Instances(/* @non_null@ */Reader reader) throws IOException {
#     ArffReader arff = new ArffReader(reader, 1000, false);
#     initialize(arff.getData(), 1000);
#     arff.setRetainStringValues(true);
#     Instance inst;
#     while ((inst = arff.readInstance(this)) != null) {
#       m_Instances.add(inst);
#     }
#     compactify();
#   }
#
#   /**
#    * Reads the header of an ARFF file from a reader and reserves space for the
#    * given number of instances. Lets the class index be undefined (negative).
#    *
#    * @param reader the reader
#    * @param capacity the capacity
#    * @throws IllegalArgumentException if the header is not read successfully or
#    *           the capacity is negative.
#    * @throws IOException if there is a problem with the reader.
#    * @deprecated instead of using this method in conjunction with the
#    *             <code>readInstance(Reader)</code> method, one should use the
#    *             <code>ArffLoader</code> or <code>DataSource</code> class
#    *             instead.
#    * @see weka.core.converters.ArffLoader
#    * @see weka.core.converters.ConverterUtils.DataSource
#    */
#   // @ requires capacity >= 0;
#   // @ ensures classIndex() == -1;
#   @Deprecated
#   public Instances(/* @non_null@ */Reader reader, int capacity) throws IOException {
#
#     ArffReader arff = new ArffReader(reader, 0);
#     Instances header = arff.getStructure();
#     initialize(header, capacity);
#     m_Lines = arff.getLineNo();
#   }
#
#   /**
#    * Constructor copying all instances and references to the header information
#    * from the given set of instances.
#    *
#    * @param dataset the set to be copied
#    */
#   public Instances(/* @non_null@ */Instances dataset) {
#
#     this(dataset, dataset.numInstances());
#
#     dataset.copyInstances(0, this, dataset.numInstances());
#   }
#
#   /**
#    * Constructor creating an empty set of instances. Copies references to the
#    * header information from the given set of instances. Sets the capacity of
#    * the set of instances to 0 if its negative.
#    *
#    * @param dataset the instances from which the header information is to be
#    *          taken
#    * @param capacity the capacity of the new dataset
#    */
#   public Instances(/* @non_null@ */Instances dataset, int capacity) {
#     initialize(dataset, capacity);
#   }
#
#   /**
#    * initializes with the header information of the given dataset and sets the
#    * capacity of the set of instances.
#    *
#    * @param dataset the dataset to use as template
#    * @param capacity the number of rows to reserve
#    */
#   protected void initialize(Instances dataset, int capacity) {
#     if (capacity < 0) {
#       capacity = 0;
#     }
#
#     // Strings only have to be "shallow" copied because
#     // they can't be modified.
#     m_ClassIndex = dataset.m_ClassIndex;
#     m_RelationName = dataset.m_RelationName;
#     m_Attributes = dataset.m_Attributes;
#     m_NamesToAttributeIndices = dataset.m_NamesToAttributeIndices;
#     m_Instances = new ArrayList<Instance>(capacity);
#   }
#
#   /**
#    * Creates a new set of instances by copying a subset of another set.
#    *
#    * @param source the set of instances from which a subset is to be created
#    * @param first the index of the first instance to be copied
#    * @param toCopy the number of instances to be copied
#    * @throws IllegalArgumentException if first and toCopy are out of range
#    */
#   // @ requires 0 <= first;
#   // @ requires 0 <= toCopy;
#   // @ requires first + toCopy <= source.numInstances();
#   public Instances(/* @non_null@ */Instances source, int first, int toCopy) {
#
#     this(source, toCopy);
#
#     if ((first < 0) || ((first + toCopy) > source.numInstances())) {
#       throw new IllegalArgumentException("Parameters first and/or toCopy out "
#         + "of range");
#     }
#     source.copyInstances(first, this, toCopy);
#   }
#
#   /**
#    * Creates an empty set of instances. Uses the given attribute information.
#    * Sets the capacity of the set of instances to 0 if its negative. Given
#    * attribute information must not be changed after this constructor has been
#    * used.
#    *
#    * @param name the name of the relation
#    * @param attInfo the attribute information
#    * @param capacity the capacity of the set
#    * @throws IllegalArgumentException if attribute names are not unique
#    */
#   public Instances(/* @non_null@ */String name,
#     /* @non_null@ */ArrayList<Attribute> attInfo, int capacity) {
#
#     // check whether the attribute names are unique
#     HashSet<String> names = new HashSet<String>();
#     StringBuffer nonUniqueNames = new StringBuffer();
#     for (Attribute att : attInfo) {
#       if (names.contains(att.name())) {
#         nonUniqueNames.append("'" + att.name() + "' ");
#       }
#       names.add(att.name());
#     }
#     if (names.size() != attInfo.size()) {
#       throw new IllegalArgumentException("Attribute names are not unique!"
#         + " Causes: " + nonUniqueNames.toString());
#     }
#     names.clear();
#
#     m_RelationName = name;
#     m_ClassIndex = -1;
#     m_Attributes = attInfo;
#     m_NamesToAttributeIndices = new HashMap<String, Integer>((int) (numAttributes() / 0.75));
#     for (int i = 0; i < numAttributes(); i++) {
#       attribute(i).setIndex(i);
#       m_NamesToAttributeIndices.put(attribute(i).name(), i);
#     }
#     m_Instances = new ArrayList<Instance>(capacity);
#   }
#
#   /**
#    * Create a copy of the structure. If the data has string or relational
#    * attributes, theses are replaced by empty copies. Other attributes are left
#    * unmodified, but the underlying list structure holding references to the attributes
#    * is shallow-copied, so that other Instances objects with a reference to this list are not affected.
#    *
#    * @return a copy of the instance structure.
#    */
#   public Instances stringFreeStructure() {
#
#     ArrayList<Attribute> newAtts = new ArrayList<Attribute>();
#     for (Attribute att : m_Attributes) {
#       if (att.type() == Attribute.STRING) {
#         newAtts.add(new Attribute(att.name(), (List<String>) null, att.index()));
#       } else if (att.type() == Attribute.RELATIONAL) {
#         newAtts.add(new Attribute(att.name(), new Instances(att.relation(), 0),
#           att.index()));
#       }
#     }
#     if (newAtts.size() == 0) {
#       return new Instances(this, 0);
#     }
#     ArrayList<Attribute> atts = Utils.cast(m_Attributes.clone());
#     for (Attribute att : newAtts) {
#       atts.set(att.index(), att);
#     }
#     Instances result = new Instances(this, 0);
#     result.m_Attributes = atts;
#     return result;
#   }
#
#   /**
#    * Adds one instance to the end of the set. Shallow copies instance before it
#    * is added. Increases the size of the dataset if it is not large enough. Does
#    * not check if the instance is compatible with the dataset. Note: String or
#    * relational values are not transferred.
#    *
#    * @param instance the instance to be added
#    */
#   @Override
#   public boolean add(/* @non_null@ */Instance instance) {
#
#     Instance newInstance = (Instance) instance.copy();
#
#     newInstance.setDataset(this);
#     m_Instances.add(newInstance);
#
#     return true;
#   }
#
#   /**
#    * Adds one instance at the given position in the list. Shallow
#    * copies instance before it is added. Increases the size of the
#    * dataset if it is not large enough. Does not check if the instance
#    * is compatible with the dataset. Note: String or relational values
#    * are not transferred.
#    *
#    * @param index position where instance is to be inserted
#    * @param instance the instance to be added
#    */
#   // @ requires 0 <= index;
#   // @ requires index < m_Instances.size();
#   @Override
#   public void add(int index, /* @non_null@ */Instance instance) {
#
#     Instance newInstance = (Instance) instance.copy();
#
#     newInstance.setDataset(this);
#     m_Instances.add(index, newInstance);
#   }
#
#   /**
#    * Returns true if all attribute weights are the same and false otherwise. Returns true if there are no attributes.
#    * The class attribute (if set) is skipped when this test is performed.
#    */
#   public boolean allAttributeWeightsIdentical() {
#
#     boolean foundOne = false;
#     double weight = 0;
#     for (int i = 0; i < numAttributes(); i++) {
#       if (i != classIndex()) {
#         if (foundOne && (attribute(i).weight() != weight)) {
#           return false;
#         } else if (!foundOne) {
#           foundOne = true;
#           weight = attribute(i).weight();
#         }
#       }
#     }
#     return true;
#   }
#
#   /**
#    * Returns true if all instance weights are the same and false otherwise. Returns true if there are no instances.
#    */
#   public boolean allInstanceWeightsIdentical() {
#
#     if (numInstances() == 0) {
#       return true;
#     } else {
#       double weight = instance(0).weight();
#       for (int i = 1; i < numInstances(); i++) {
#         if (instance(i).weight() != weight) {
#           return false;
#         }
#       }
#       return true;
#     }
#   }
#
#   /**
#    * Returns an attribute.
#    *
#    * @param index the attribute's index (index starts with 0)
#    * @return the attribute at the given position
#    */
#   // @ requires 0 <= index;
#   // @ requires index < m_Attributes.size();
#   // @ ensures \result != null;
#   public/* @pure@ */Attribute attribute(int index) {
#
#     return m_Attributes.get(index);
#   }
#
#   /**
#    * Returns an attribute given its name. If there is more than one attribute
#    * with the same name, it returns the first one. Returns null if the attribute
#    * can't be found.
#    *
#    * @param name the attribute's name
#    * @return the attribute with the given name, null if the attribute can't be
#    *         found
#    */
#   public/* @pure@ */Attribute attribute(String name) {
#
#     Integer index = m_NamesToAttributeIndices.get(name);
#     if (index != null) {
#       return attribute(index);
#     }
#
#     return null;
#   }
#
#   /**
#    * Checks for attributes of the given type in the dataset
#    *
#    * @param attType the attribute type to look for
#    * @return true if attributes of the given type are present
#    */
#   public boolean checkForAttributeType(int attType) {
#
#     int i = 0;
#
#     while (i < m_Attributes.size()) {
#       if (attribute(i++).type() == attType) {
#         return true;
#       }
#     }
#     return false;
#   }
#
#   /**
#    * Checks for string attributes in the dataset
#    *
#    * @return true if string attributes are present, false otherwise
#    */
#   public/* @pure@ */boolean checkForStringAttributes() {
#     return checkForAttributeType(Attribute.STRING);
#   }
#
#   /**
#    * Checks if the given instance is compatible with this dataset. Only looks at
#    * the size of the instance and the ranges of the values for nominal and
#    * string attributes.
#    *
#    * @param instance the instance to check
#    * @return true if the instance is compatible with the dataset
#    */
#   public/* @pure@ */boolean checkInstance(Instance instance) {
#
#     if (instance.numAttributes() != numAttributes()) {
#       return false;
#     }
#     for (int i = 0; i < numAttributes(); i++) {
#       if (instance.isMissing(i)) {
#         continue;
#       } else if (attribute(i).isNominal() || attribute(i).isString()) {
#         if (instance.value(i) != (int) instance.value(i)) {
#           return false;
#         } else if ((instance.value(i) < 0)
#           || (instance.value(i) > attribute(i).numValues() - 1)) {
#           return false;
#         }
#       }
#     }
#     return true;
#   }
#
#   /**
#    * Returns the class attribute.
#    *
#    * @return the class attribute
#    * @throws UnassignedClassException if the class is not set
#    */
#   // @ requires classIndex() >= 0;
#   public/* @pure@ */Attribute classAttribute() {
#
#     if (m_ClassIndex < 0) {
#       throw new UnassignedClassException("Class index is negative (not set)!");
#     }
#     return attribute(m_ClassIndex);
#   }
#
#   /**
#    * Returns the class attribute's index. Returns negative number if it's
#    * undefined.
#    *
#    * @return the class index as an integer
#    */
#   // ensures \result == m_ClassIndex;
#   public/* @pure@ */int classIndex() {
#
#     return m_ClassIndex;
#   }
#
#   /**
#    * Compactifies the set of instances. Decreases the capacity of the set so
#    * that it matches the number of instances in the set.
#    */
#   public void compactify() {
#
#     m_Instances.trimToSize();
#   }
#
#   /**
#    * Removes all instances from the set.
#    */
#   public void delete() {
#
#     m_Instances = new ArrayList<Instance>();
#   }
#
#   /**
#    * Removes an instance at the given position from the set.
#    *
#    * @param index the instance's position (index starts with 0)
#    */
#   // @ requires 0 <= index && index < numInstances();
#   public void delete(int index) {
#
#     m_Instances.remove(index);
#   }
#
#   /**
#    * Deletes an attribute at the given position (0 to numAttributes()
#    * - 1). Attribute objects after the deletion point are copied so
#    * that their indices can be decremented. Creates a fresh list to
#    * hold the old and new attribute objects.
#    * @param position the attribute's position (position starts with 0)
#    * @throws IllegalArgumentException if the given index is out of range or the
#    *           class attribute is being deleted
#    */
#   // @ requires 0 <= position && position < numAttributes();
#   // @ requires position != classIndex();
#   public void deleteAttributeAt(int position) {
#
#     if ((position < 0) || (position >= m_Attributes.size())) {
#       throw new IllegalArgumentException("Cannot delete attribute: index out of range");
#     }
#     if (position == m_ClassIndex) {
#       throw new IllegalArgumentException("Cannot delete class attribute");
#     }
#
#     ArrayList<Attribute> newList = new ArrayList<Attribute>(m_Attributes.size() - 1);
#     HashMap<String, Integer> newMap = new HashMap<String, Integer>((int) ((m_Attributes.size() - 1) / 0.75));
#     for (int i = 0 ; i < position; i++) {
#       Attribute att = m_Attributes.get(i);
#       newList.add(att);
#       newMap.put(att.name(), i);
#     }
#     for (int i = position + 1; i < m_Attributes.size(); i++) {
#       Attribute newAtt = (Attribute) m_Attributes.get(i).copy();
#       newAtt.setIndex(i - 1);
#       newList.add(newAtt);
#       newMap.put(newAtt.name(), i - 1);
#     }
#     m_Attributes = newList;
#     m_NamesToAttributeIndices = newMap;
#
#     if (m_ClassIndex > position) {
#       m_ClassIndex--;
#     }
#     for (int i = 0; i < numInstances(); i++) {
#       instance(i).setDataset(null);
#       instance(i).deleteAttributeAt(position);
#       instance(i).setDataset(this);
#     }
#   }
#
#   /**
#    * Deletes all attributes of the given type in the dataset. A deep copy of the
#    * attribute information is performed before an attribute is deleted.
#    *
#    * @param attType the attribute type to delete
#    * @throws IllegalArgumentException if attribute couldn't be successfully
#    *           deleted (probably because it is the class attribute).
#    */
#   public void deleteAttributeType(int attType) {
#     int i = 0;
#     while (i < m_Attributes.size()) {
#       if (attribute(i).type() == attType) {
#         deleteAttributeAt(i);
#       } else {
#         i++;
#       }
#     }
#   }
#
#   /**
#    * Deletes all string attributes in the dataset. A deep copy of the attribute
#    * information is performed before an attribute is deleted.
#    *
#    * @throws IllegalArgumentException if string attribute couldn't be
#    *           successfully deleted (probably because it is the class
#    *           attribute).
#    * @see #deleteAttributeType(int)
#    */
#   public void deleteStringAttributes() {
#     deleteAttributeType(Attribute.STRING);
#   }
#
#   /**
#    * Removes all instances with missing values for a particular attribute from
#    * the dataset.
#    *
#    * @param attIndex the attribute's index (index starts with 0)
#    */
#   // @ requires 0 <= attIndex && attIndex < numAttributes();
#   public void deleteWithMissing(int attIndex) {
#
#     ArrayList<Instance> newInstances = new ArrayList<Instance>(numInstances());
#
#     for (int i = 0; i < numInstances(); i++) {
#       if (!instance(i).isMissing(attIndex)) {
#         newInstances.add(instance(i));
#       }
#     }
#     m_Instances = newInstances;
#   }
#
#   /**
#    * Removes all instances with missing values for a particular attribute from
#    * the dataset.
#    *
#    * @param att the attribute
#    */
#   public void deleteWithMissing(/* @non_null@ */Attribute att) {
#
#     deleteWithMissing(att.index());
#   }
#
#   /**
#    * Removes all instances with a missing class value from the dataset.
#    *
#    * @throws UnassignedClassException if class is not set
#    */
#   public void deleteWithMissingClass() {
#
#     if (m_ClassIndex < 0) {
#       throw new UnassignedClassException("Class index is negative (not set)!");
#     }
#     deleteWithMissing(m_ClassIndex);
#   }
#
#   /**
#    * Returns an enumeration of all the attributes. The class attribute (if set)
#    * is skipped by this enumeration.
#    *
#    * @return enumeration of all the attributes.
#    */
#   public/* @non_null pure@ */Enumeration<Attribute> enumerateAttributes() {
#
#     return new WekaEnumeration<Attribute>(m_Attributes, m_ClassIndex);
#   }
#
#   /**
#    * Returns an enumeration of all instances in the dataset.
#    *
#    * @return enumeration of all instances in the dataset
#    */
#   public/* @non_null pure@ */Enumeration<Instance> enumerateInstances() {
#
#     return new WekaEnumeration<Instance>(m_Instances);
#   }
#
#   /**
#    * Checks if two headers are equivalent. If not, then returns a message why
#    * they differ.
#    *
#    * @param dataset another dataset
#    * @return null if the header of the given dataset is equivalent to this
#    *         header, otherwise a message with details on why they differ
#    */
#   public String equalHeadersMsg(Instances dataset) {
#     // Check class and all attributes
#     if (m_ClassIndex != dataset.m_ClassIndex) {
#       return "Class index differ: " + (m_ClassIndex + 1) + " != "
#         + (dataset.m_ClassIndex + 1);
#     }
#
#     if (m_Attributes.size() != dataset.m_Attributes.size()) {
#       return "Different number of attributes: " + m_Attributes.size() + " != "
#         + dataset.m_Attributes.size();
#     }
#
#     for (int i = 0; i < m_Attributes.size(); i++) {
#       String msg = attribute(i).equalsMsg(dataset.attribute(i));
#       if (msg != null) {
#         return "Attributes differ at position " + (i + 1) + ":\n" + msg;
#       }
#     }
#
#     return null;
#   }
#
#   /**
#    * Checks if two headers are equivalent.
#    *
#    * @param dataset another dataset
#    * @return true if the header of the given dataset is equivalent to this
#    *         header
#    */
#   public/* @pure@ */boolean equalHeaders(Instances dataset) {
#     return (equalHeadersMsg(dataset) == null);
#   }
#
#   /**
#    * Returns the first instance in the set.
#    *
#    * @return the first instance in the set
#    */
#   // @ requires numInstances() > 0;
#   public/* @non_null pure@ */Instance firstInstance() {
#
#     return m_Instances.get(0);
#   }
#
#   /**
#    * Returns a random number generator. The initial seed of the random number
#    * generator depends on the given seed and the hash code of a string
#    * representation of a instances chosen based on the given seed.
#    *
#    * @param seed the given seed
#    * @return the random number generator
#    */
#   public Random getRandomNumberGenerator(long seed) {
#
#     Random r = new Random(seed);
#     r.setSeed(instance(r.nextInt(numInstances())).toStringNoWeight().hashCode()
#       + seed);
#     return r;
#   }
#
#   /**
#    * Inserts an attribute at the given position (0 to numAttributes())
#    * and sets all values to be missing. Shallow copies the attribute
#    * before it is inserted. Existing attribute objects at and after
#    * the insertion point are also copied so that their indices can be
#    * incremented. Creates a fresh list to hold the old and new
#    * attribute objects.
#    *
#    * @param att the attribute to be inserted
#    * @param position the attribute's position (position starts with 0)
#    * @throws IllegalArgumentException if the given index is out of range
#    */
#   // @ requires 0 <= position;
#   // @ requires position <= numAttributes();
#   public void insertAttributeAt(/* @non_null@ */Attribute att, int position) {
#
#     if ((position < 0) || (position > m_Attributes.size())) {
#       throw new IllegalArgumentException("Cannot insert attribute: index out of range");
#     }
#     Attribute existingAttribute = attribute(att.name());
#     if (existingAttribute != null) {
#       throw new IllegalArgumentException("Cannot insert attribute: name '" + att.name() + "' already in use in the " +
#               Utils.indexToOrdinal(existingAttribute.index()) + " attribute " + existingAttribute);
#     }
#     att = (Attribute) att.copy();
#     att.setIndex(position);
#
#     ArrayList<Attribute> newList = new ArrayList<Attribute>(m_Attributes.size() + 1);
#     HashMap<String, Integer> newMap = new HashMap<String, Integer>((int) ((m_Attributes.size() + 1) / 0.75));
#     for (int i = 0 ; i < position; i++) {
#       Attribute oldAtt = m_Attributes.get(i);
#       newList.add(oldAtt);
#       newMap.put(oldAtt.name(), i);
#     }
#     newList.add(att);
#     newMap.put(att.name(), position);
#     for (int i = position; i < m_Attributes.size(); i++) {
#       Attribute newAtt = (Attribute) m_Attributes.get(i).copy();
#       newAtt.setIndex(i + 1);
#       newList.add(newAtt);
#       newMap.put(newAtt.name(), i + 1);
#     }
#     m_Attributes = newList;
#     m_NamesToAttributeIndices = newMap;
#
#     for (int i = 0; i < numInstances(); i++) {
#       instance(i).setDataset(null);
#       instance(i).insertAttributeAt(position);
#       instance(i).setDataset(this);
#     }
#     if (m_ClassIndex >= position) {
#       m_ClassIndex++;
#     }
#   }
#
#   /**
#    * Returns the instance at the given position.
#    *
#    * @param index the instance's index (index starts with 0)
#    * @return the instance at the given position
#    */
#   // @ requires 0 <= index;
#   // @ requires index < numInstances();
#   public/* @non_null pure@ */Instance instance(int index) {
#
#     return m_Instances.get(index);
#   }
#
#   /**
#    * Returns the instance at the given position.
#    *
#    * @param index the instance's index (index starts with 0)
#    * @return the instance at the given position
#    */
#   // @ requires 0 <= index;
#   // @ requires index < numInstances();
#   @Override
#   public/* @non_null pure@ */Instance get(int index) {
#
#     return m_Instances.get(index);
#   }
#
#   /**
#    * Returns the kth-smallest attribute value of a numeric attribute.
#    *
#    * @param att the Attribute object
#    * @param k the value of k
#    * @return the kth-smallest value
#    */
#   public double kthSmallestValue(Attribute att, int k) {
#
#     return kthSmallestValue(att.index(), k);
#   }
#
#   /**
#    * Returns the kth-smallest attribute value of a numeric attribute. NOTE
#    * CHANGE: Missing values (NaN values) are now treated as Double.MAX_VALUE.
#    * Also, the order of the instances in the data is no longer affected.
#    *
#    * @param attIndex the attribute's index
#    * @param k the value of k
#    * @return the kth-smallest value
#    */
#   public double kthSmallestValue(int attIndex, int k) {
#
#     if (!attribute(attIndex).isNumeric()) {
#       throw new IllegalArgumentException(
#         "Instances: attribute must be numeric to compute kth-smallest value.");
#     }
#
#     if ((k < 1) || (k > numInstances())) {
#       throw new IllegalArgumentException(
#         "Instances: value for k for computing kth-smallest value too large.");
#     }
#
#     double[] vals = new double[numInstances()];
#     for (int i = 0; i < vals.length; i++) {
#       double val = instance(i).value(attIndex);
#       if (Utils.isMissingValue(val)) {
#         vals[i] = Double.MAX_VALUE;
#       } else {
#         vals[i] = val;
#       }
#     }
#     return Utils.kthSmallestValue(vals, k);
#   }
#
#   /**
#    * Returns the last instance in the set.
#    *
#    * @return the last instance in the set
#    */
#   // @ requires numInstances() > 0;
#   public/* @non_null pure@ */Instance lastInstance() {
#
#     return m_Instances.get(m_Instances.size() - 1);
#   }
#
#   /**
#    * Returns the mean (mode) for a numeric (nominal) attribute as a
#    * floating-point value. Returns 0 if the attribute is neither nominal nor
#    * numeric. If all values are missing it returns zero.
#    *
#    * @param attIndex the attribute's index (index starts with 0)
#    * @return the mean or the mode
#    */
#   public/* @pure@ */double meanOrMode(int attIndex) {
#
#     double result, found;
#     int[] counts;
#
#     if (attribute(attIndex).isNumeric()) {
#       result = found = 0;
#       for (int j = 0; j < numInstances(); j++) {
#         if (!instance(j).isMissing(attIndex)) {
#           found += instance(j).weight();
#           result += instance(j).weight() * instance(j).value(attIndex);
#         }
#       }
#       if (found <= 0) {
#         return 0;
#       } else {
#         return result / found;
#       }
#     } else if (attribute(attIndex).isNominal()) {
#       counts = new int[attribute(attIndex).numValues()];
#       for (int j = 0; j < numInstances(); j++) {
#         if (!instance(j).isMissing(attIndex)) {
#           counts[(int) instance(j).value(attIndex)] += instance(j).weight();
#         }
#       }
#       return Utils.maxIndex(counts);
#     } else {
#       return 0;
#     }
#   }
#
#   /**
#    * Returns the mean (mode) for a numeric (nominal) attribute as a
#    * floating-point value. Returns 0 if the attribute is neither nominal nor
#    * numeric. If all values are missing it returns zero.
#    *
#    * @param att the attribute
#    * @return the mean or the mode
#    */
#   public/* @pure@ */double meanOrMode(Attribute att) {
#
#     return meanOrMode(att.index());
#   }
#
#   /**
#    * Returns the number of attributes.
#    *
#    * @return the number of attributes as an integer
#    */
#   // @ ensures \result == m_Attributes.size();
#   public/* @pure@ */int numAttributes() {
#
#     return m_Attributes.size();
#   }
#
#   /**
#    * Returns the number of class labels.
#    *
#    * @return the number of class labels as an integer if the class attribute is
#    *         nominal, 1 otherwise.
#    * @throws UnassignedClassException if the class is not set
#    */
#   // @ requires classIndex() >= 0;
#   public/* @pure@ */int numClasses() {
#
#     if (m_ClassIndex < 0) {
#       throw new UnassignedClassException("Class index is negative (not set)!");
#     }
#     if (!classAttribute().isNominal()) {
#       return 1;
#     } else {
#       return classAttribute().numValues();
#     }
#   }
#
#   /**
#    * Returns the number of distinct values of a given attribute. The value
#    * 'missing' is not counted.
#    *
#    * @param attIndex the attribute (index starts with 0)
#    * @return the number of distinct values of a given attribute
#    */
#   // @ requires 0 <= attIndex;
#   // @ requires attIndex < numAttributes();
#   public/* @pure@ */int numDistinctValues(int attIndex) {
#
#     HashSet<Double> set = new HashSet<Double>(2 * numInstances());
#     for (Instance current : this) {
#       double key = current.value(attIndex);
#       if (!Utils.isMissingValue(key)) {
#         set.add(key);
#       }
#     }
#     return set.size();
#   }
#
#   /**
#    * Returns the number of distinct values of a given attribute. The value
#    * 'missing' is not counted.
#    *
#    * @param att the attribute
#    * @return the number of distinct values of a given attribute
#    */
#   public/* @pure@ */int numDistinctValues(/* @non_null@ */Attribute att) {
#
#     return numDistinctValues(att.index());
#   }
#
#   /**
#    * Returns the number of instances in the dataset.
#    *
#    * @return the number of instances in the dataset as an integer
#    */
#   // @ ensures \result == m_Instances.size();
#   public/* @pure@ */int numInstances() {
#
#     return m_Instances.size();
#   }
#
#   /**
#    * Returns the number of instances in the dataset.
#    *
#    * @return the number of instances in the dataset as an integer
#    */
#   // @ ensures \result == m_Instances.size();
#   @Override
#   public/* @pure@ */int size() {
#
#     return m_Instances.size();
#   }
#
#   /**
#    * Shuffles the instances in the set so that they are ordered randomly.
#    *
#    * @param random a random number generator
#    */
#   public void randomize(Random random) {
#
#     for (int j = numInstances() - 1; j > 0; j--) {
#       swap(j, random.nextInt(j + 1));
#     }
#   }
#
#   /**
#    * Reads a single instance from the reader and appends it to the dataset.
#    * Automatically expands the dataset if it is not large enough to hold the
#    * instance. This method does not check for carriage return at the end of the
#    * line.
#    *
#    * @param reader the reader
#    * @return false if end of file has been reached
#    * @throws IOException if the information is not read successfully
#    * @deprecated instead of using this method in conjunction with the
#    *             <code>readInstance(Reader)</code> method, one should use the
#    *             <code>ArffLoader</code> or <code>DataSource</code> class
#    *             instead.
#    * @see weka.core.converters.ArffLoader
#    * @see weka.core.converters.ConverterUtils.DataSource
#    */
#   @Deprecated
#   public boolean readInstance(Reader reader) throws IOException {
#
#     ArffReader arff = new ArffReader(reader, this, m_Lines, 1);
#     Instance inst = arff.readInstance(arff.getData(), false);
#     m_Lines = arff.getLineNo();
#     if (inst != null) {
#       add(inst);
#       return true;
#     } else {
#       return false;
#     }
#   }
#
#   /**
#    * Replaces the attribute at the given position (0 to
#    * numAttributes()) with the given attribute and sets all its values to
#    * be missing. Shallow copies the given attribute before it is
#    * inserted. Creates a fresh list to hold the old and new
#    * attribute objects.
#    *
#    * @param att the attribute to be inserted
#    * @param position the attribute's position (position starts with 0)
#    * @throws IllegalArgumentException if the given index is out of range
#    */
#   // @ requires 0 <= position;
#   // @ requires position <= numAttributes();
#   public void replaceAttributeAt(/* @non_null@ */Attribute att, int position) {
#
#     if ((position < 0) || (position >= m_Attributes.size())) {
#       throw new IllegalArgumentException("Cannot replace attribute: index out of range");
#     }
#     // Does the new attribute have a different name than the attribute it replaces?
#     if (!att.name().equals(m_Attributes.get(position).name())) {
#
#       // Need to check if attribute name already exists at a different position
#       Attribute candidate = attribute(att.name());
#       if (candidate != null) {
#         throw new IllegalArgumentException("Cannot replace attribute: name '" + att.name() + "' already in use in the "
#                 + Utils.indexToOrdinal(candidate.index()) + " attribute " + candidate);
#       }
#     }
#     att = (Attribute) att.copy();
#     att.setIndex(position);
#
#     ArrayList<Attribute> newList = new ArrayList<Attribute>(m_Attributes.size());
#     HashMap<String, Integer> newMap = new HashMap<String, Integer>((int) ((m_Attributes.size() + 1) / 0.75));
#     for (int i = 0 ; i < position; i++) {
#       Attribute oldAtt = m_Attributes.get(i);
#       newList.add(oldAtt);
#       newMap.put(oldAtt.name(), i);
#     }
#     newList.add(att);
#     newMap.put(att.name(), position);
#     for (int i = position + 1; i < m_Attributes.size(); i++) {
#       Attribute newAtt = (Attribute) m_Attributes.get(i);
#       newList.add(newAtt);
#       newMap.put(newAtt.name(), i);
#     }
#     m_Attributes = newList;
#     m_NamesToAttributeIndices = newMap;
#
#     for (int i = 0; i < numInstances(); i++) {
#       instance(i).setDataset(null);
#       instance(i).setMissing(position);
#       instance(i).setDataset(this);
#     }
#   }
#
#   /**
#    * Returns the relation's name.
#    *
#    * @return the relation's name as a string
#    */
#   // @ ensures \result == m_RelationName;
#   public/* @pure@ */String relationName() {
#
#     return m_RelationName;
#   }
#
#   /**
#    * Removes the instance at the given position.
#    *
#    * @param index the instance's index (index starts with 0)
#    * @return the instance at the given position
#    */
#   // @ requires 0 <= index;
#   // @ requires index < numInstances();
#   @Override
#   public Instance remove(int index) {
#
#     return m_Instances.remove(index);
#   }
#
#   /**
#    * Renames an attribute. This change only affects this dataset.
#    *
#    * @param att the attribute's index (index starts with 0)
#    * @param name the new name
#    */
#   public void renameAttribute(int att, String name) {
#
#     if ((att < 0) || (att >= m_Attributes.size())) {
#       throw new IllegalArgumentException("Cannot rename attribute: index out of range");
#     }
#     Attribute existingAtt = attribute(name);
#     if (existingAtt != null) {
#       if (att == existingAtt.index()) {
#         return; // Old name is equal to new name so that is fine
#       } else {
#         throw new IllegalArgumentException("Cannot rename attribute: name '" + name + "' already in use in the " +
#                 Utils.indexToOrdinal(existingAtt.index()) + " attribute " + existingAtt);
#       }
#     }
#
#     Attribute newAtt = attribute(att).copy(name);
#     ArrayList<Attribute> newVec = new ArrayList<Attribute>(numAttributes());
#     HashMap<String, Integer> newMap = new HashMap<String, Integer>((int)(numAttributes() / 0.75));
#     for (Attribute attr : m_Attributes) {
#       if (attr.index() == att) {
#         newVec.add(newAtt);
#         newMap.put(name, att);
#       } else {
#         newVec.add(attr);
#         newMap.put(attr.name(), attr.index());
#       }
#     }
#     m_Attributes = newVec;
#     m_NamesToAttributeIndices = newMap;
#   }
#
#   /**
#    * Sets the weight of an attribute. This change only affects this dataset.
#    *
#    * @param att the attribute
#    * @param weight the new weight
#    */
#   public void setAttributeWeight(Attribute att, double weight) {
#
#     setAttributeWeight(att.index(), weight);
#   }
#
#   /**
#    * Sets the weight of an attribute. This change only affects this dataset.
#    *
#    * @param att the attribute's index (index starts with 0)
#    * @param weight the new weight
#    */
#   public void setAttributeWeight(int att, double weight) {
#
#     Attribute existingAtt = attribute(att);
#     if (existingAtt.weight() == weight) {
#       return;
#     }
#
#     Attribute newAtt = (Attribute)existingAtt.copy();
#     newAtt.setWeight(weight);
#     ArrayList<Attribute> newVec = new ArrayList<Attribute>(numAttributes());
#     HashMap<String, Integer> newMap = new HashMap<String, Integer>((int)(numAttributes() / 0.75));
#     for (Attribute attr : m_Attributes) {
#       if (attr.index() == att) {
#         newVec.add(newAtt);
#         newMap.put(newAtt.name(), att);
#       } else {
#         newVec.add(attr);
#         newMap.put(attr.name(), attr.index());
#       }
#     }
#     m_Attributes = newVec;
#     m_NamesToAttributeIndices = newMap;
#   }
#
#   /**
#    * Renames an attribute. This change only affects this dataset.
#    *
#    * @param att the attribute
#    * @param name the new name
#    */
#   public void renameAttribute(Attribute att, String name) {
#
#     renameAttribute(att.index(), name);
#   }
#
#   /**
#    * Renames the value of a nominal (or string) attribute value. This change
#    * only affects this dataset.
#    *
#    * @param att the attribute's index (index starts with 0)
#    * @param val the value's index (index starts with 0)
#    * @param name the new name
#    */
#   public void renameAttributeValue(int att, int val, String name) {
#
#     Attribute newAtt = (Attribute) attribute(att).copy();
#     ArrayList<Attribute> newVec = new ArrayList<Attribute>(numAttributes());
#
#     newAtt.setValue(val, name);
#     for (Attribute attr : m_Attributes) {
#       if (attr.index() == att) {
#         newVec.add(newAtt);
#       } else {
#         newVec.add(attr);
#       }
#     }
#     m_Attributes = newVec;
#   }
#
#   /**
#    * Renames the value of a nominal (or string) attribute value. This change
#    * only affects this dataset.
#    *
#    * @param att the attribute
#    * @param val the value
#    * @param name the new name
#    */
#   public void renameAttributeValue(Attribute att, String val, String name) {
#
#     int v = att.indexOfValue(val);
#     if (v == -1) {
#       throw new IllegalArgumentException(val + " not found");
#     }
#     renameAttributeValue(att.index(), v, name);
#   }
#
#   /**
#    * Creates a new dataset of the same size as this dataset using random sampling with
#    * replacement.
#    *
#    * @param random a random number generator
#    * @return the new dataset
#    */
#   public Instances resample(Random random) {
#
#     Instances newData = new Instances(this, numInstances());
#     while (newData.numInstances() < numInstances()) {
#       newData.add(instance(random.nextInt(numInstances())));
#     }
#     return newData;
#   }
#
#   /**
#    * Creates a new dataset of the same size as this dataset using random sampling with
#    * replacement according to the current instance weights. The weights of the
#    * instances in the new dataset are set to one. See also
#    * resampleWithWeights(Random, double[], boolean[]).
#    *
#    * @param random a random number generator
#    * @return the new dataset
#    */
#   public Instances resampleWithWeights(Random random) {
#
#     return resampleWithWeights(random, false);
#   }
#
#   /**
#    * Creates a new dataset of the same size as this dataset using random sampling with
#    * replacement according to the current instance weights. The weights of the
#    * instances in the new dataset are set to one. See also
#    * resampleWithWeights(Random, double[], boolean[]).
#    *
#    * @param random a random number generator
#    * @param sampled an array indicating what has been sampled
#    * @return the new dataset
#    */
#   public Instances resampleWithWeights(Random random, boolean[] sampled) {
#
#     return resampleWithWeights(random, sampled, false);
#   }
#
#   /**
#    * Creates a new dataset of the same size as this dataset using random sampling with
#    * replacement according to the current instance weights. See also
#    * resampleWithWeights(Random, double[], boolean[]).
#    *
#    * @param random a random number generator
#    * @param representUsingWeights if true, copies are represented using weights
#    *          in resampled data
#    * @return the new dataset
#    */
#   public Instances resampleWithWeights(Random random,
#     boolean representUsingWeights) {
#
#     return resampleWithWeights(random, null, representUsingWeights);
#   }
#
#   /**
#    * Creates a new dataset of the same size as this dataset using random sampling with
#    * replacement according to the current instance weights. See also
#    * resampleWithWeights(Random, double[], boolean[]).
#    *
#    * @param random a random number generator
#    * @param sampled an array indicating what has been sampled
#    * @param representUsingWeights if true, copies are represented using weights
#    *          in resampled data
#    * @return the new dataset
#    */
#   public Instances resampleWithWeights(Random random, boolean[] sampled,
#     boolean representUsingWeights) {
#
#     return resampleWithWeights(random, sampled, representUsingWeights, 100.0);
#   }
#
#   /**
#    * Creates a new dataset from this dataset using random sampling with
#    * replacement according to current instance weights. The size of the sample
#    * can be specified as a percentage of this dataset. See also
#    * resampleWithWeights(Random, double[], boolean[]).
#    *
#    * @param random a random number generator
#    * @param sampled an array indicating what has been sampled, can be null
#    * @param representUsingWeights if true, copies are represented using weights
#    *          in resampled data
#    * @param sampleSize size of the new dataset as a percentage of the size of this
#    *                   dataset
#    * @return the new dataset
#    * @throws IllegalArgumentException if the weights array is of the wrong
#    *           length or contains negative weights.
#    */
#   public Instances resampleWithWeights(Random random,
#                                        boolean[] sampled, boolean representUsingWeights, double sampleSize) {
#
#     double[] weights = new double[numInstances()];
#     for (int i = 0; i < weights.length; i++) {
#       weights[i] = instance(i).weight();
#     }
#     return resampleWithWeights(random, weights, sampled, representUsingWeights, sampleSize);
#   }
#
#   /**
#    * Creates a new dataset of the same size as this dataset using random sampling with
#    * replacement according to the given weight vector. The weights of the
#    * instances in the new dataset are set to one. The length of the weight
#    * vector has to be the same as the number of instances in the dataset, and
#    * all weights have to be positive. See also
#    * resampleWithWeights(Random, double[], boolean[]).
#    *
#    * @param random a random number generator
#    * @param weights the weight vector
#    * @return the new dataset
#    * @throws IllegalArgumentException if the weights array is of the wrong
#    *           length or contains negative weights.
#    */
#   public Instances resampleWithWeights(Random random, double[] weights) {
#
#     return resampleWithWeights(random, weights, null);
#   }
#
#   /**
#    * Creates a new dataset of the same size as this dataset using random sampling with
#    * replacement according to the given weight vector. The weights of the
#    * instances in the new dataset are set to one. The length of the weight
#    * vector has to be the same as the number of instances in the dataset, and
#    * all weights have to be positive. Uses Walker's method, see pp. 232 of
#    * "Stochastic Simulation" by B.D. Ripley (1987).
#    *
#    * @param random a random number generator
#    * @param weights the weight vector
#    * @param sampled an array indicating what has been sampled, can be null
#    * @return the new dataset
#    * @throws IllegalArgumentException if the weights array is of the wrong
#    *           length or contains negative weights.
#    */
#   public Instances resampleWithWeights(Random random, double[] weights,
#     boolean[] sampled) {
#
#     return resampleWithWeights(random, weights, sampled, false);
#   }
#
#   /**
#    * Creates a new dataset of the same size as this dataset using random sampling with
#    * replacement according to the given weight vector. The length of the weight
#    * vector has to be the same as the number of instances in the dataset, and
#    * all weights have to be positive. Uses Walker's method, see pp. 232 of
#    * "Stochastic Simulation" by B.D. Ripley (1987).
#    *
#    * @param random a random number generator
#    * @param weights the weight vector
#    * @param sampled an array indicating what has been sampled, can be null
#    * @param representUsingWeights if true, copies are represented using weights
#    *          in resampled data
#    * @return the new dataset
#    * @throws IllegalArgumentException if the weights array is of the wrong
#    *           length or contains negative weights.
#    */
#   public Instances resampleWithWeights(Random random, double[] weights,
#                                        boolean[] sampled, boolean representUsingWeights) {
#
#     return resampleWithWeights(random, weights, sampled, representUsingWeights, 100.0);
#   }
#
#   /**
#    * Creates a new dataset from this dataset using random sampling with
#    * replacement according to the given weight vector. The length of the weight
#    * vector has to be the same as the number of instances in the dataset, and
#    * all weights have to be positive. Uses Walker's method, see pp. 232 of
#    * "Stochastic Simulation" by B.D. Ripley (1987). The size of the sample
#    * can be specified as a percentage of this dataset.
#    *
#    * @param random a random number generator
#    * @param weights the weight vector
#    * @param sampled an array indicating what has been sampled, can be null
#    * @param representUsingWeights if true, copies are represented using weights
#    *          in resampled data
#    * @param sampleSize size of the new dataset as a percentage of the size of this
#    *                   dataset
#    * @return the new dataset
#    * @throws IllegalArgumentException if the weights array is of the wrong
#    *           length or contains negative weights.
#    */
#   public Instances resampleWithWeights(Random random, double[] weights,
#     boolean[] sampled, boolean representUsingWeights, double sampleSize) {
#
#     if (weights.length != numInstances()) {
#       throw new IllegalArgumentException("weights.length != numInstances.");
#     }
#
#     if ((sampleSize < 0) || (sampleSize > 100)) {
#       throw new IllegalArgumentException("Sample size must be a percentage.");
#     }
#
#     Instances newData = new Instances(this, numInstances());
#     if (numInstances() == 0) {
#       return newData;
#     }
#
#     // Walker's method, see pp. 232 of "Stochastic Simulation" by B.D. Ripley
#     double[] P = new double[weights.length];
#     System.arraycopy(weights, 0, P, 0, weights.length);
#     Utils.normalize(P);
#     double[] Q = new double[weights.length];
#     int[] A = new int[weights.length];
#     int[] W = new int[weights.length];
#     int M = weights.length;
#     int NN = -1;
#     int NP = M;
#     for (int I = 0; I < M; I++) {
#       if (P[I] < 0) {
#         throw new IllegalArgumentException("Weights have to be positive.");
#       }
#       Q[I] = M * P[I];
#       if (Q[I] < 1.0) {
#         W[++NN] = I;
#       } else {
#         W[--NP] = I;
#       }
#     }
#     if (NN > -1 && NP < M) {
#       for (int S = 0; S < M - 1; S++) {
#         int I = W[S];
#         int J = W[NP];
#         A[I] = J;
#         Q[J] += Q[I] - 1.0;
#         if (Q[J] < 1.0) {
#           NP++;
#         }
#         if (NP >= M) {
#           break;
#         }
#       }
#       // A[W[M]] = W[M];
#     }
#
#     for (int I = 0; I < M; I++) {
#       Q[I] += I;
#     }
#
#     // Do we need to keep track of how many copies to use?
#     int[] counts = null;
#     if (representUsingWeights) {
#       counts = new int[M];
#     }
#
#     int numToBeSampled = (int) (numInstances() * (sampleSize / 100.0));
#
#     for (int i = 0; i < numToBeSampled; i++) {
#       int ALRV;
#       double U = M * random.nextDouble();
#       int I = (int) U;
#       if (U < Q[I]) {
#         ALRV = I;
#       } else {
#         ALRV = A[I];
#       }
#       if (representUsingWeights) {
#         counts[ALRV]++;
#       } else {
#         newData.add(instance(ALRV));
#       }
#       if (sampled != null) {
#         sampled[ALRV] = true;
#       }
#       if (!representUsingWeights) {
#         newData.instance(newData.numInstances() - 1).setWeight(1);
#       }
#     }
#
#     // Add data based on counts if weights should represent numbers of copies.
#     if (representUsingWeights) {
#       for (int i = 0; i < counts.length; i++) {
#         if (counts[i] > 0) {
#           newData.add(instance(i));
#           newData.instance(newData.numInstances() - 1).setWeight(counts[i]);
#         }
#       }
#     }
#
#     return newData;
#   }
#
#   /**
#    * Replaces the instance at the given position. Shallow copies instance before
#    * it is added. Does not check if the instance is compatible with the dataset.
#    * Note: String or relational values are not transferred.
#    *
#    * @param index position where instance is to be inserted
#    * @param instance the instance to be inserted
#    * @return the instance previously at that position
#    */
#   // @ requires 0 <= index;
#   // @ requires index < m_Instances.size();
#   @Override
#   public Instance set(int index, /* @non_null@ */Instance instance) {
#
#     Instance newInstance = (Instance) instance.copy();
#     Instance oldInstance = m_Instances.get(index);
#
#     newInstance.setDataset(this);
#     m_Instances.set(index, newInstance);
#
#     return oldInstance;
#   }
#
#   /**
#    * Sets the class attribute.
#    *
#    * @param att attribute to be the class
#    */
#   public void setClass(Attribute att) {
#
#     m_ClassIndex = att.index();
#   }
#
#   /**
#    * Sets the class index of the set. If the class index is negative there is
#    * assumed to be no class. (ie. it is undefined)
#    *
#    * @param classIndex the new class index (index starts with 0)
#    * @throws IllegalArgumentException if the class index is too big or < 0
#    */
#   public void setClassIndex(int classIndex) {
#
#     if (classIndex >= numAttributes()) {
#       throw new IllegalArgumentException("Invalid class index: " + classIndex);
#     }
#     m_ClassIndex = classIndex;
#   }
#
#   /**
#    * Sets the relation's name.
#    *
#    * @param newName the new relation name.
#    */
#   public void setRelationName(/* @non_null@ */String newName) {
#
#     m_RelationName = newName;
#   }
#
#   /**
#    * Sorts a nominal attribute (stable, linear-time sort). Instances
#    * are sorted based on the attribute label ordering specified in the header.
#    *
#    * @param attIndex the attribute's index (index starts with 0)
#    */
#   protected void sortBasedOnNominalAttribute(int attIndex) {
#
#     // Figure out number of instances for each attribute value
#     // and store original list of instances away
#     int[] counts = new int[attribute(attIndex).numValues()];
#     Instance[] backup = new Instance[numInstances()];
#     int j = 0;
#     for (Instance inst : this) {
#       backup[j++] = inst;
#       if (!inst.isMissing(attIndex)) {
#         counts[(int)inst.value(attIndex)]++;
#       }
#     }
#
#     // Indices to figure out where to add instances
#     int[] indices = new int[counts.length];
#     int start = 0;
#     for (int i = 0; i < counts.length; i++) {
#       indices[i] = start;
#       start += counts[i];
#     }
#     for (Instance inst : backup) { // Use backup here
#       if (!inst.isMissing(attIndex)) {
#         m_Instances.set(indices[(int)inst.value(attIndex)]++, inst);
#       } else {
#         m_Instances.set(start++, inst);
#       }
#     }
#   }
#
#   /**
#    * Sorts the instances based on an attribute. For numeric attributes,
#    * instances are sorted in ascending order. For nominal attributes, instances
#    * are sorted based on the attribute label ordering specified in the header.
#    * Instances with missing values for the attribute are placed at the end of
#    * the dataset.
#    *
#    * @param attIndex the attribute's index (index starts with 0)
#    */
#   public void sort(int attIndex) {
#
#     if (!attribute(attIndex).isNominal()) {
#
#       // Use quicksort from Utils class for sorting
#       double[] vals = new double[numInstances()];
#       Instance[] backup = new Instance[vals.length];
#       for (int i = 0; i < vals.length; i++) {
#         Instance inst = instance(i);
#         backup[i] = inst;
#         double val = inst.value(attIndex);
#         if (Utils.isMissingValue(val)) {
#           vals[i] = Double.MAX_VALUE;
#         } else {
#           vals[i] = val;
#         }
#       }
#
#       int[] sortOrder = Utils.sortWithNoMissingValues(vals);
#       for (int i = 0; i < vals.length; i++) {
#         m_Instances.set(i, backup[sortOrder[i]]);
#       }
#     } else {
#       sortBasedOnNominalAttribute(attIndex);
#     }
#   }
#
#   /**
#    * Sorts the instances based on an attribute. For numeric attributes,
#    * instances are sorted into ascending order. For nominal attributes,
#    * instances are sorted based on the attribute label ordering specified in the
#    * header. Instances with missing values for the attribute are placed at the
#    * end of the dataset.
#    *
#    * @param att the attribute
#    */
#   public void sort(Attribute att) {
#
#     sort(att.index());
#   }
#
#   /**
#    * Sorts the instances based on an attribute, using a stable sort. For numeric attributes,
#    * instances are sorted in ascending order. For nominal attributes, instances
#    * are sorted based on the attribute label ordering specified in the header.
#    * Instances with missing values for the attribute are placed at the end of
#    * the dataset.
#    *
#    * @param attIndex the attribute's index (index starts with 0)
#    */
#   public void stableSort(int attIndex) {
#
#     if (!attribute(attIndex).isNominal()) {
#
#       // Use quicksort from Utils class for sorting
#       double[] vals = new double[numInstances()];
#       Instance[] backup = new Instance[vals.length];
#       for (int i = 0; i < vals.length; i++) {
#         Instance inst = instance(i);
#         backup[i] = inst;
#         vals[i] = inst.value(attIndex);
#       }
#
#       int[] sortOrder = Utils.stableSort(vals);
#       for (int i = 0; i < vals.length; i++) {
#         m_Instances.set(i, backup[sortOrder[i]]);
#       }
#     } else {
#       sortBasedOnNominalAttribute(attIndex);
#     }
#   }
#
#   /**
#    * Sorts the instances based on an attribute, using a stable sort. For numeric attributes,
#    * instances are sorted into ascending order. For nominal attributes,
#    * instances are sorted based on the attribute label ordering specified in the
#    * header. Instances with missing values for the attribute are placed at the
#    * end of the dataset.
#    *
#    * @param att the attribute
#    */
#   public void stableSort(Attribute att) {
#
#     stableSort(att.index());
#   }
#
#   /**
#    * Stratifies a set of instances according to its class values if the class
#    * attribute is nominal (so that afterwards a stratified cross-validation can
#    * be performed).
#    *
#    * @param numFolds the number of folds in the cross-validation
#    * @throws UnassignedClassException if the class is not set
#    */
#   public void stratify(int numFolds) {
#
#     if (numFolds <= 1) {
#       throw new IllegalArgumentException(
#         "Number of folds must be greater than 1");
#     }
#     if (m_ClassIndex < 0) {
#       throw new UnassignedClassException("Class index is negative (not set)!");
#     }
#     if (classAttribute().isNominal()) {
#
#       // sort by class
#       int index = 1;
#       while (index < numInstances()) {
#         Instance instance1 = instance(index - 1);
#         for (int j = index; j < numInstances(); j++) {
#           Instance instance2 = instance(j);
#           if ((instance1.classValue() == instance2.classValue())
#             || (instance1.classIsMissing() && instance2.classIsMissing())) {
#             swap(index, j);
#             index++;
#           }
#         }
#         index++;
#       }
#       stratStep(numFolds);
#     }
#   }
#
#   /**
#    * Computes the sum of all the instances' weights.
#    *
#    * @return the sum of all the instances' weights as a double
#    */
#   public/* @pure@ */double sumOfWeights() {
#
#     double sum = 0;
#
#     for (int i = 0; i < numInstances(); i++) {
#       sum += instance(i).weight();
#     }
#     return sum;
#   }
#
#   /**
#    * Creates the test set for one fold of a cross-validation on the dataset.
#    *
#    * @param numFolds the number of folds in the cross-validation. Must be
#    *          greater than 1.
#    * @param numFold 0 for the first fold, 1 for the second, ...
#    * @return the test set as a set of weighted instances
#    * @throws IllegalArgumentException if the number of folds is less than 2 or
#    *           greater than the number of instances.
#    */
#   // @ requires 2 <= numFolds && numFolds < numInstances();
#   // @ requires 0 <= numFold && numFold < numFolds;
#   public Instances testCV(int numFolds, int numFold) {
#
#     int numInstForFold, first, offset;
#     Instances test;
#
#     if (numFolds < 2) {
#       throw new IllegalArgumentException("Number of folds must be at least 2!");
#     }
#     if (numFolds > numInstances()) {
#       throw new IllegalArgumentException(
#         "Can't have more folds than instances!");
#     }
#     numInstForFold = numInstances() / numFolds;
#     if (numFold < numInstances() % numFolds) {
#       numInstForFold++;
#       offset = numFold;
#     } else {
#       offset = numInstances() % numFolds;
#     }
#     test = new Instances(this, numInstForFold);
#     first = numFold * (numInstances() / numFolds) + offset;
#     copyInstances(first, test, numInstForFold);
#     return test;
#   }
#
#   /**
#    * Returns the dataset as a string in ARFF format. Strings are quoted if they
#    * contain whitespace characters, or if they are a question mark.
#    *
#    * @return the dataset in ARFF format as a string
#    */
#   @Override
#   public String toString() {
#
#     StringBuffer text = new StringBuffer();
#
#     text.append(ARFF_RELATION).append(" ").append(Utils.quote(m_RelationName))
#     .append("\n\n");
#     for (int i = 0; i < numAttributes(); i++) {
#       text.append(attribute(i)).append("\n");
#     }
#     text.append("\n").append(ARFF_DATA).append("\n");
#
#     text.append(stringWithoutHeader());
#     return text.toString();
#   }
#
#   /**
#    * Returns the instances in the dataset as a string in ARFF format. Strings
#    * are quoted if they contain whitespace characters, or if they are a question
#    * mark.
#    *
#    * @return the dataset in ARFF format as a string
#    */
#   protected String stringWithoutHeader() {
#
#     StringBuffer text = new StringBuffer();
#
#     for (int i = 0; i < numInstances(); i++) {
#       text.append(instance(i));
#       if (i < numInstances() - 1) {
#         text.append('\n');
#       }
#     }
#     return text.toString();
#   }
#
#   /**
#    * Creates the training set for one fold of a cross-validation on the dataset.
#    *
#    * @param numFolds the number of folds in the cross-validation. Must be
#    *          greater than 1.
#    * @param numFold 0 for the first fold, 1 for the second, ...
#    * @return the training set
#    * @throws IllegalArgumentException if the number of folds is less than 2 or
#    *           greater than the number of instances.
#    */
#   // @ requires 2 <= numFolds && numFolds < numInstances();
#   // @ requires 0 <= numFold && numFold < numFolds;
#   public Instances trainCV(int numFolds, int numFold) {
#
#     int numInstForFold, first, offset;
#     Instances train;
#
#     if (numFolds < 2) {
#       throw new IllegalArgumentException("Number of folds must be at least 2!");
#     }
#     if (numFolds > numInstances()) {
#       throw new IllegalArgumentException(
#         "Can't have more folds than instances!");
#     }
#     numInstForFold = numInstances() / numFolds;
#     if (numFold < numInstances() % numFolds) {
#       numInstForFold++;
#       offset = numFold;
#     } else {
#       offset = numInstances() % numFolds;
#     }
#     train = new Instances(this, numInstances() - numInstForFold);
#     first = numFold * (numInstances() / numFolds) + offset;
#     copyInstances(0, train, first);
#     copyInstances(first + numInstForFold, train, numInstances() - first
#       - numInstForFold);
#
#     return train;
#   }
#
#   /**
#    * Creates the training set for one fold of a cross-validation on the dataset.
#    * The data is subsequently randomized based on the given random number
#    * generator.
#    *
#    * @param numFolds the number of folds in the cross-validation. Must be
#    *          greater than 1.
#    * @param numFold 0 for the first fold, 1 for the second, ...
#    * @param random the random number generator
#    * @return the training set
#    * @throws IllegalArgumentException if the number of folds is less than 2 or
#    *           greater than the number of instances.
#    */
#   // @ requires 2 <= numFolds && numFolds < numInstances();
#   // @ requires 0 <= numFold && numFold < numFolds;
#   public Instances trainCV(int numFolds, int numFold, Random random) {
#
#     Instances train = trainCV(numFolds, numFold);
#     train.randomize(random);
#     return train;
#   }
#
#   /**
#    * Computes the variance for all numeric attributes simultaneously.
#    * This is faster than calling variance() for each attribute.
#    * The resulting array has as many dimensions as there are attributes.
#    * Array elements corresponding to non-numeric attributes are set to 0.
#    *
#    * @return the array containing the variance values
#    */
#   public/* @pure@ */double[] variances() {
#
#     double[] vars = new double[numAttributes()];
#
#     for (int i = 0; i < numAttributes(); i++)
#       vars[i] = Double.NaN;
#
#     double[] means = new double[numAttributes()];
#     double[] sumWeights = new double[numAttributes()];
#
#     for (int i = 0; i < numInstances(); i++) {
#       double weight = instance(i).weight();
#       for (int attIndex = 0; attIndex < numAttributes(); attIndex++) {
#         if (attribute(attIndex).isNumeric()) {
#           if (!instance(i).isMissing(attIndex)) {
#             double value = instance(i).value(attIndex);
#
#             if (Double.isNaN(vars[attIndex])) {
#               // For the first value the mean can suffer from loss of precision
#               // so we treat it separately and make sure the calculation stays accurate
#               means[attIndex] = value;
#               sumWeights[attIndex] = weight;
#               vars[attIndex] = 0;
#               continue;
#             }
#
#             double delta = weight*(value - means[attIndex]);
#             sumWeights[attIndex] += weight;
#             means[attIndex] += delta/sumWeights[attIndex];
#             vars[attIndex] += delta*(value - means[attIndex]);
#           }
#         }
#       }
#     }
#
#     for (int attIndex = 0; attIndex < numAttributes(); attIndex++) {
#       if (attribute(attIndex).isNumeric()) {
#         if (sumWeights[attIndex] <= 1) {
#           vars[attIndex] = Double.NaN;
#         } else {
#           vars[attIndex] /= sumWeights[attIndex] - 1;
#           if (vars[attIndex] < 0)
#             vars[attIndex] = 0;
#         }
#       }
#     }
#
#     return vars;
#   }
#
#   /**
#    * Computes the variance for a numeric attribute.
#    *
#    * @param attIndex the numeric attribute (index starts with 0)
#    * @return the variance if the attribute is numeric
#    * @throws IllegalArgumentException if the attribute is not numeric
#    */
#   public/* @pure@ */double variance(int attIndex) {
#
#     if (!attribute(attIndex).isNumeric()) {
#       throw new IllegalArgumentException(
#         "Can't compute variance because attribute is " + "not numeric!");
#     }
#
#     double mean = 0;
#     double var = Double.NaN;
#     double sumWeights = 0;
#     for (int i = 0; i < numInstances(); i++) {
#       if (!instance(i).isMissing(attIndex)) {
#         double weight = instance(i).weight();
#         double value = instance(i).value(attIndex);
#
#         if (Double.isNaN(var)) {
#           // For the first value the mean can suffer from loss of precision
#           // so we treat it separately and make sure the calculation stays accurate
#           mean = value;
#           sumWeights = weight;
#           var = 0;
#           continue;
#         }
#
#         double delta = weight*(value - mean);
#         sumWeights += weight;
#         mean += delta/sumWeights;
#         var += delta*(value - mean);
#       }
#     }
#
#     if (sumWeights <= 1) {
#       return Double.NaN;
#     }
#
#     var /= sumWeights - 1;
#
#     // We don't like negative variance
#     if (var < 0) {
#       return 0;
#     } else {
#       return var;
#     }
#   }
#
#   /**
#    * Computes the variance for a numeric attribute.
#    *
#    * @param att the numeric attribute
#    * @return the variance if the attribute is numeric
#    * @throws IllegalArgumentException if the attribute is not numeric
#    */
#   public/* @pure@ */double variance(Attribute att) {
#
#     return variance(att.index());
#   }
#
#   /**
#    * Calculates summary statistics on the values that appear in this set of
#    * instances for a specified attribute.
#    *
#    * @param index the index of the attribute to summarize (index starts with 0)
#    * @return an AttributeStats object with it's fields calculated.
#    */
#   // @ requires 0 <= index && index < numAttributes();
#   public AttributeStats attributeStats(int index) {
#
#     AttributeStats result = new AttributeStats();
#     if (attribute(index).isNominal()) {
#       result.nominalCounts = new int[attribute(index).numValues()];
#       result.nominalWeights = new double[attribute(index).numValues()];
#     }
#     if (attribute(index).isNumeric()) {
#       result.numericStats = new weka.experiment.Stats();
#     }
#     result.totalCount = numInstances();
#
#     HashMap<Double,double[]> map = new HashMap<Double,double[]>(2 * result.totalCount);
#     for (Instance current : this) {
#       double key = current.value(index);
#       if (Utils.isMissingValue(key)) {
#         result.missingCount++;
#       } else {
#         double[] values = map.get(key);
#         if (values == null) {
#           values = new double[2];
#           values[0] = 1.0;
#           values[1] = current.weight();
#           map.put(key, values);
#         } else {
#           values[0]++;
#           values[1] += current.weight();
#         }
#       }
#     }
#
#     for (Entry<Double, double[]> entry : map.entrySet()) {
#       result.addDistinct(entry.getKey(), (int)entry.getValue()[0], entry.getValue()[1]);
#     }
#     return result;
#   }
#
#   /**
#    * Gets the value of all instances in this dataset for a particular attribute.
#    * Useful in conjunction with Utils.sort to allow iterating through the
#    * dataset in sorted order for some attribute.
#    *
#    * @param index the index of the attribute.
#    * @return an array containing the value of the desired attribute for each
#    *         instance in the dataset.
#    */
#   // @ requires 0 <= index && index < numAttributes();
#   public/* @pure@ */double[] attributeToDoubleArray(int index) {
#
#     double[] result = new double[numInstances()];
#     for (int i = 0; i < result.length; i++) {
#       result[i] = instance(i).value(index);
#     }
#     return result;
#   }
#
#   /**
#    * Generates a string summarizing the set of instances. Gives a breakdown for
#    * each attribute indicating the number of missing/discrete/unique values and
#    * other information.
#    *
#    * @return a string summarizing the dataset
#    */
#   public String toSummaryString() {
#
#     StringBuffer result = new StringBuffer();
#     result.append("Relation Name:  ").append(relationName()).append('\n');
#     result.append("Num Instances:  ").append(numInstances()).append('\n');
#     result.append("Num Attributes: ").append(numAttributes()).append('\n');
#     result.append('\n');
#
#     result.append(Utils.padLeft("", 5)).append(Utils.padRight("Name", 25));
#     result.append(Utils.padLeft("Type", 5)).append(Utils.padLeft("Nom", 5));
#     result.append(Utils.padLeft("Int", 5)).append(Utils.padLeft("Real", 5));
#     result.append(Utils.padLeft("Missing", 12));
#     result.append(Utils.padLeft("Unique", 12));
#     result.append(Utils.padLeft("Dist", 6)).append('\n');
#
#     // Figure out how many digits we need for the index
#     int numDigits = (int)Math.log10((int)numAttributes()) + 1;
#
#     for (int i = 0; i < numAttributes(); i++) {
#       Attribute a = attribute(i);
#       AttributeStats as = attributeStats(i);
#       result.append(Utils.padLeft("" + (i + 1), numDigits)).append(' ');
#       result.append(Utils.padRight(a.name(), 25)).append(' ');
#       long percent;
#       switch (a.type()) {
#       case Attribute.NOMINAL:
#         result.append(Utils.padLeft("Nom", 4)).append(' ');
#         percent = Math.round(100.0 * as.intCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         result.append(Utils.padLeft("" + 0, 3)).append("% ");
#         percent = Math.round(100.0 * as.realCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         break;
#       case Attribute.NUMERIC:
#         result.append(Utils.padLeft("Num", 4)).append(' ');
#         result.append(Utils.padLeft("" + 0, 3)).append("% ");
#         percent = Math.round(100.0 * as.intCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         percent = Math.round(100.0 * as.realCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         break;
#       case Attribute.DATE:
#         result.append(Utils.padLeft("Dat", 4)).append(' ');
#         result.append(Utils.padLeft("" + 0, 3)).append("% ");
#         percent = Math.round(100.0 * as.intCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         percent = Math.round(100.0 * as.realCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         break;
#       case Attribute.STRING:
#         result.append(Utils.padLeft("Str", 4)).append(' ');
#         percent = Math.round(100.0 * as.intCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         result.append(Utils.padLeft("" + 0, 3)).append("% ");
#         percent = Math.round(100.0 * as.realCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         break;
#       case Attribute.RELATIONAL:
#         result.append(Utils.padLeft("Rel", 4)).append(' ');
#         percent = Math.round(100.0 * as.intCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         result.append(Utils.padLeft("" + 0, 3)).append("% ");
#         percent = Math.round(100.0 * as.realCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         break;
#       default:
#         result.append(Utils.padLeft("???", 4)).append(' ');
#         result.append(Utils.padLeft("" + 0, 3)).append("% ");
#         percent = Math.round(100.0 * as.intCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         percent = Math.round(100.0 * as.realCount / as.totalCount);
#         result.append(Utils.padLeft("" + percent, 3)).append("% ");
#         break;
#       }
#       result.append(Utils.padLeft("" + as.missingCount, 5)).append(" /");
#       percent = Math.round(100.0 * as.missingCount / as.totalCount);
#       result.append(Utils.padLeft("" + percent, 3)).append("% ");
#       result.append(Utils.padLeft("" + as.uniqueCount, 5)).append(" /");
#       percent = Math.round(100.0 * as.uniqueCount / as.totalCount);
#       result.append(Utils.padLeft("" + percent, 3)).append("% ");
#       result.append(Utils.padLeft("" + as.distinctCount, 5)).append(' ');
#       result.append('\n');
#     }
#     return result.toString();
#   }
#
#   /**
#    * Copies instances from one set to the end of another one.
#    *
#    * @param from the position of the first instance to be copied
#    * @param dest the destination for the instances
#    * @param num the number of instances to be copied
#    */
#   // @ requires 0 <= from && from <= numInstances() - num;
#   // @ requires 0 <= num;
#   protected void copyInstances(int from, /* @non_null@ */Instances dest, int num) {
#
#     for (int i = 0; i < num; i++) {
#       dest.add(instance(from + i));
#     }
#   }
#
#   /**
#    * Returns string including all instances, their weights and their indices in
#    * the original dataset.
#    *
#    * @return description of instance and its weight as a string
#    */
#   protected/* @pure@ */String instancesAndWeights() {
#
#     StringBuffer text = new StringBuffer();
#
#     for (int i = 0; i < numInstances(); i++) {
#       text.append(instance(i) + " " + instance(i).weight());
#       if (i < numInstances() - 1) {
#         text.append("\n");
#       }
#     }
#     return text.toString();
#   }
#
#   /**
#    * Help function needed for stratification of set.
#    *
#    * @param numFolds the number of folds for the stratification
#    */
#   protected void stratStep(int numFolds) {
#
#     ArrayList<Instance> newVec = new ArrayList<Instance>(m_Instances.size());
#     int start = 0, j;
#
#     // create stratified batch
#     while (newVec.size() < numInstances()) {
#       j = start;
#       while (j < numInstances()) {
#         newVec.add(instance(j));
#         j = j + numFolds;
#       }
#       start++;
#     }
#     m_Instances = newVec;
#   }
#
#   /**
#    * Swaps two instances in the set.
#    *
#    * @param i the first instance's index (index starts with 0)
#    * @param j the second instance's index (index starts with 0)
#    */
#   // @ requires 0 <= i && i < numInstances();
#   // @ requires 0 <= j && j < numInstances();
#   public void swap(int i, int j) {
#
#     Instance in = m_Instances.get(i);
#     m_Instances.set(i, m_Instances.get(j));
#     m_Instances.set(j, in);
#   }
#
#   /**
#    * Merges two sets of Instances together. The resulting set will have all the
#    * attributes of the first set plus all the attributes of the second set. The
#    * number of instances in both sets must be the same.
#    *
#    * @param first the first set of Instances
#    * @param second the second set of Instances
#    * @return the merged set of Instances
#    * @throws IllegalArgumentException if the datasets are not the same size
#    */
#   public static Instances mergeInstances(Instances first, Instances second) {
#
#     if (first.numInstances() != second.numInstances()) {
#       throw new IllegalArgumentException(
#         "Instance sets must be of the same size");
#     }
#
#     // Create the vector of merged attributes
#     ArrayList<Attribute> newAttributes = new ArrayList<Attribute>(first.numAttributes() +
#       second.numAttributes());
#     for (Attribute att : first.m_Attributes) {
#       newAttributes.add(att);
#     }
#     for (Attribute att : second.m_Attributes) {
#       newAttributes.add((Attribute)att.copy()); // Need to copy because indices will change.
#     }
#
#     // Create the set of Instances
#     Instances merged = new Instances(first.relationName() + '_'
#       + second.relationName(), newAttributes, first.numInstances());
#     // Merge each instance
#     for (int i = 0; i < first.numInstances(); i++) {
#       merged.add(first.instance(i).mergeInstance(second.instance(i)));
#     }
#     return merged;
#   }
#
#   /**
#    * Method for testing this class.
#    *
#    * @param argv should contain one element: the name of an ARFF file
#    */
#   // @ requires argv != null;
#   // @ requires argv.length == 1;
#   // @ requires argv[0] != null;
#   public static void test(String[] argv) {
#
#     Instances instances, secondInstances, train, test, empty;
#     Random random = new Random(2);
#     Reader reader;
#     int start, num;
#     ArrayList<Attribute> testAtts;
#     ArrayList<String> testVals;
#     int i, j;
#
#     try {
#       if (argv.length > 1) {
#         throw (new Exception("Usage: Instances [<filename>]"));
#       }
#
#       // Creating set of instances from scratch
#       testVals = new ArrayList<String>(2);
#       testVals.add("first_value");
#       testVals.add("second_value");
#       testAtts = new ArrayList<Attribute>(2);
#       testAtts.add(new Attribute("nominal_attribute", testVals));
#       testAtts.add(new Attribute("numeric_attribute"));
#       instances = new Instances("test_set", testAtts, 10);
#       instances.add(new DenseInstance(instances.numAttributes()));
#       instances.add(new DenseInstance(instances.numAttributes()));
#       instances.add(new DenseInstance(instances.numAttributes()));
#       instances.setClassIndex(0);
#       System.out.println("\nSet of instances created from scratch:\n");
#       System.out.println(instances);
#
#       if (argv.length == 1) {
#         String filename = argv[0];
#         reader = new FileReader(filename);
#
#         // Read first five instances and print them
#         System.out.println("\nFirst five instances from file:\n");
#         instances = new Instances(reader, 1);
#         instances.setClassIndex(instances.numAttributes() - 1);
#         i = 0;
#         while ((i < 5) && (instances.readInstance(reader))) {
#           i++;
#         }
#         System.out.println(instances);
#
#         // Read all the instances in the file
#         reader = new FileReader(filename);
#         instances = new Instances(reader);
#
#         // Make the last attribute be the class
#         instances.setClassIndex(instances.numAttributes() - 1);
#
#         // Print header and instances.
#         System.out.println("\nDataset:\n");
#         System.out.println(instances);
#         System.out.println("\nClass index: " + instances.classIndex());
#       }
#
#       // Test basic methods based on class index.
#       System.out.println("\nClass name: " + instances.classAttribute().name());
#       System.out.println("\nClass index: " + instances.classIndex());
#       System.out.println("\nClass is nominal: "
#         + instances.classAttribute().isNominal());
#       System.out.println("\nClass is numeric: "
#         + instances.classAttribute().isNumeric());
#       System.out.println("\nClasses:\n");
#       for (i = 0; i < instances.numClasses(); i++) {
#         System.out.println(instances.classAttribute().value(i));
#       }
#       System.out.println("\nClass values and labels of instances:\n");
#       for (i = 0; i < instances.numInstances(); i++) {
#         Instance inst = instances.instance(i);
#         System.out.print(inst.classValue() + "\t");
#         System.out.print(inst.toString(inst.classIndex()));
#         if (instances.instance(i).classIsMissing()) {
#           System.out.println("\tis missing");
#         } else {
#           System.out.println();
#         }
#       }
#
#       // Create random weights.
#       System.out.println("\nCreating random weights for instances.");
#       for (i = 0; i < instances.numInstances(); i++) {
#         instances.instance(i).setWeight(random.nextDouble());
#       }
#
#       // Print all instances and their weights (and the sum of weights).
#       System.out.println("\nInstances and their weights:\n");
#       System.out.println(instances.instancesAndWeights());
#       System.out.print("\nSum of weights: ");
#       System.out.println(instances.sumOfWeights());
#
#       // Insert an attribute
#       secondInstances = new Instances(instances);
#       Attribute testAtt = new Attribute("Inserted");
#       secondInstances.insertAttributeAt(testAtt, 0);
#       System.out.println("\nSet with inserted attribute:\n");
#       System.out.println(secondInstances);
#       System.out.println("\nClass name: "
#         + secondInstances.classAttribute().name());
#
#       // Delete the attribute
#       secondInstances.deleteAttributeAt(0);
#       System.out.println("\nSet with attribute deleted:\n");
#       System.out.println(secondInstances);
#       System.out.println("\nClass name: "
#         + secondInstances.classAttribute().name());
#
#       // Test if headers are equal
#       System.out.println("\nHeaders equal: "
#         + instances.equalHeaders(secondInstances) + "\n");
#
#       // Print data in internal format.
#       System.out.println("\nData (internal values):\n");
#       for (i = 0; i < instances.numInstances(); i++) {
#         for (j = 0; j < instances.numAttributes(); j++) {
#           if (instances.instance(i).isMissing(j)) {
#             System.out.print("? ");
#           } else {
#             System.out.print(instances.instance(i).value(j) + " ");
#           }
#         }
#         System.out.println();
#       }
#
#       // Just print header
#       System.out.println("\nEmpty dataset:\n");
#       empty = new Instances(instances, 0);
#       System.out.println(empty);
#       System.out.println("\nClass name: " + empty.classAttribute().name());
#
#       // Create copy and rename an attribute and a value (if possible)
#       if (empty.classAttribute().isNominal()) {
#         Instances copy = new Instances(empty, 0);
#         copy.renameAttribute(copy.classAttribute(), "new_name");
#         copy.renameAttributeValue(copy.classAttribute(), copy.classAttribute()
#           .value(0), "new_val_name");
#         System.out.println("\nDataset with names changed:\n" + copy);
#         System.out.println("\nOriginal dataset:\n" + empty);
#       }
#
#       // Create and prints subset of instances.
#       start = instances.numInstances() / 4;
#       num = instances.numInstances() / 2;
#       System.out.print("\nSubset of dataset: ");
#       System.out.println(num + " instances from " + (start + 1) + ". instance");
#       secondInstances = new Instances(instances, start, num);
#       System.out.println("\nClass name: "
#         + secondInstances.classAttribute().name());
#
#       // Print all instances and their weights (and the sum of weights).
#       System.out.println("\nInstances and their weights:\n");
#       System.out.println(secondInstances.instancesAndWeights());
#       System.out.print("\nSum of weights: ");
#       System.out.println(secondInstances.sumOfWeights());
#
#       // Create and print training and test sets for 3-fold
#       // cross-validation.
#       System.out.println("\nTrain and test folds for 3-fold CV:");
#       if (instances.classAttribute().isNominal()) {
#         instances.stratify(3);
#       }
#       for (j = 0; j < 3; j++) {
#         train = instances.trainCV(3, j, new Random(1));
#         test = instances.testCV(3, j);
#
#         // Print all instances and their weights (and the sum of weights).
#         System.out.println("\nTrain: ");
#         System.out.println("\nInstances and their weights:\n");
#         System.out.println(train.instancesAndWeights());
#         System.out.print("\nSum of weights: ");
#         System.out.println(train.sumOfWeights());
#         System.out.println("\nClass name: " + train.classAttribute().name());
#         System.out.println("\nTest: ");
#         System.out.println("\nInstances and their weights:\n");
#         System.out.println(test.instancesAndWeights());
#         System.out.print("\nSum of weights: ");
#         System.out.println(test.sumOfWeights());
#         System.out.println("\nClass name: " + test.classAttribute().name());
#       }
#
#       // Randomize instances and print them.
#       System.out.println("\nRandomized dataset:");
#       instances.randomize(random);
#
#       // Print all instances and their weights (and the sum of weights).
#       System.out.println("\nInstances and their weights:\n");
#       System.out.println(instances.instancesAndWeights());
#       System.out.print("\nSum of weights: ");
#       System.out.println(instances.sumOfWeights());
#
#       // Sort instances according to first attribute and
#       // print them.
#       System.out.print("\nInstances sorted according to first attribute:\n ");
#       instances.sort(0);
#
#       // Print all instances and their weights (and the sum of weights).
#       System.out.println("\nInstances and their weights:\n");
#       System.out.println(instances.instancesAndWeights());
#       System.out.print("\nSum of weights: ");
#       System.out.println(instances.sumOfWeights());
#     } catch (Exception e) {
#       e.printStackTrace();
#     }
#   }
#
#   /**
#    * Main method for this class. The following calls are possible:
#    * <ul>
#    * <li>
#    * <code>weka.core.Instances</code> help<br/>
#    * prints a short list of possible commands.</li>
#    * <li>
#    * <code>weka.core.Instances</code> &lt;filename&gt;<br/>
#    * prints a summary of a set of instances.</li>
#    * <li>
#    * <code>weka.core.Instances</code> merge &lt;filename1&gt; &lt;filename2&gt;<br/>
#    * merges the two datasets (must have same number of instances) and outputs
#    * the results on stdout.</li>
#    * <li>
#    * <code>weka.core.Instances</code> append &lt;filename1&gt; &lt;filename2&gt;
#    * <br/>
#    * appends the second dataset to the first one (must have same headers) and
#    * outputs the results on stdout.</li>
#    * <li>
#    * <code>weka.core.Instances</code> headers &lt;filename1&gt;
#    * &lt;filename2&gt;<br/>
#    * Compares the headers of the two datasets and prints whether they match or
#    * not.</li>
#    * <li>
#    * <code>weka.core.Instances</code> randomize &lt;seed&gt; &lt;filename&gt;<br/>
#    * randomizes the dataset with the given seed and outputs the result on
#    * stdout.</li>
#    * </ul>
#    *
#    * @param args the commandline parameters
#    */
#   public static void main(String[] args) {
#
#     try {
#       Instances i;
#       // read from stdin and print statistics
#       if (args.length == 0) {
#         DataSource source = new DataSource(System.in);
#         i = source.getDataSet();
#         System.out.println(i.toSummaryString());
#       }
#       // read file and print statistics
#       else if ((args.length == 1) && (!args[0].equals("-h"))
#         && (!args[0].equals("help"))) {
#         DataSource source = new DataSource(args[0]);
#         i = source.getDataSet();
#         System.out.println(i.toSummaryString());
#       }
#       // read two files, merge them and print result to stdout
#       else if ((args.length == 3) && (args[0].toLowerCase().equals("merge"))) {
#         DataSource source1 = new DataSource(args[1]);
#         DataSource source2 = new DataSource(args[2]);
#         i = Instances
#           .mergeInstances(source1.getDataSet(), source2.getDataSet());
#         System.out.println(i);
#       }
#       // read two files, append them and print result to stdout
#       else if ((args.length == 3) && (args[0].toLowerCase().equals("append"))) {
#         DataSource source1 = new DataSource(args[1]);
#         DataSource source2 = new DataSource(args[2]);
#         String msg = source1.getStructure().equalHeadersMsg(
#           source2.getStructure());
#         if (msg != null) {
#           throw new Exception("The two datasets have different headers:\n"
#             + msg);
#         }
#         Instances structure = source1.getStructure();
#         System.out.println(source1.getStructure());
#         while (source1.hasMoreElements(structure)) {
#           System.out.println(source1.nextElement(structure));
#         }
#         structure = source2.getStructure();
#         while (source2.hasMoreElements(structure)) {
#           System.out.println(source2.nextElement(structure));
#         }
#       }
#       // read two files and compare their headers
#       else if ((args.length == 3) && (args[0].toLowerCase().equals("headers"))) {
#         DataSource source1 = new DataSource(args[1]);
#         DataSource source2 = new DataSource(args[2]);
#         String msg = source1.getStructure().equalHeadersMsg(
#           source2.getStructure());
#         if (msg == null) {
#           System.out.println("Headers match");
#         } else {
#           System.out.println("Headers don't match:\n" + msg);
#         }
#       }
#       // read file and seed value, randomize data and print result to stdout
#       else if ((args.length == 3)
#         && (args[0].toLowerCase().equals("randomize"))) {
#         DataSource source = new DataSource(args[2]);
#         i = source.getDataSet();
#         i.randomize(new Random(Integer.parseInt(args[1])));
#         System.out.println(i);
#       }
#       // wrong parameters or help
#       else {
#         System.err
#         .println("\nUsage:\n"
#           // help
#           + "\tweka.core.Instances help\n"
#           + "\t\tPrints this help\n"
#           // stats
#           + "\tweka.core.Instances <filename>\n"
#           + "\t\tOutputs dataset statistics\n"
#           // merge
#           + "\tweka.core.Instances merge <filename1> <filename2>\n"
#           + "\t\tMerges the datasets (must have same number of rows).\n"
#           + "\t\tGenerated dataset gets output on stdout.\n"
#           // append
#           + "\tweka.core.Instances append <filename1> <filename2>\n"
#           + "\t\tAppends the second dataset to the first (must have same number of attributes).\n"
#           + "\t\tGenerated dataset gets output on stdout.\n"
#           // headers
#           + "\tweka.core.Instances headers <filename1> <filename2>\n"
#           + "\t\tCompares the structure of the two datasets and outputs whether they\n"
#           + "\t\tdiffer or not.\n"
#           // randomize
#           + "\tweka.core.Instances randomize <seed> <filename>\n"
#           + "\t\tRandomizes the dataset and outputs it on stdout.\n");
#       }
#     } catch (Exception ex) {
#       ex.printStackTrace();
#       System.err.println(ex.getMessage());
#     }
#   }
#
#   /**
#    * Returns the revision string.
#    *
#    * @return the revision
#    */
#   @Override
#   public String getRevision() {
#     return RevisionUtils.extract("$Revision: 15569 $");
#   }
# }
#
# /*
#  *   This program is free software: you can redistribute it and/or modify
#  *   it under the terms of the GNU General Public License as published by
#  *   the Free Software Foundation, either version 3 of the License, or
#  *   (at your option) any later version.
#  *
#  *   This program is distributed in the hope that it will be useful,
#  *   but WITHOUT ANY WARRANTY; without even the implied warranty of
#  *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  *   GNU General Public License for more details.
#  *
#  *   You should have received a copy of the GNU General Public License
#  *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  */
#
# /*
#  *    Copyable.java
#  *    Copyright (C) 1999-2012 University of Waikato, Hamilton, New Zealand
#  *
#  */
#
# package weka.core;
#
# /**
#  * Interface implemented by classes that can produce "shallow" copies
#  * of their objects. (As opposed to clone(), which is supposed to
#  * produce a "deep" copy.)
#  *
#  * @author Eibe Frank (eibe@cs.waikato.ac.nz)
#  * @version $Revision: 8034 $
#  */
# public interface Copyable {
#
#   /**
#    * This method produces a shallow copy of an object.
#    * It does the same as the clone() method in Object, which also produces
#    * a shallow copy.
#    */
#   Object copy();
# }
#
# /*
#  *   This program is free software: you can redistribute it and/or modify
#  *   it under the terms of the GNU General Public License as published by
#  *   the Free Software Foundation, either version 3 of the License, or
#  *   (at your option) any later version.
#  *
#  *   This program is distributed in the hope that it will be useful,
#  *   but WITHOUT ANY WARRANTY; without even the implied warranty of
#  *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  *   GNU General Public License for more details.
#  *
#  *   You should have received a copy of the GNU General Public License
#  *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  */
#
# /*
#  *    Instance.java
#  *    Copyright (C) 1999-2012 University of Waikato, Hamilton, New Zealand
#  *
#  */
#
# package weka.core;
#
# import java.util.Enumeration;
#
# /**
#  * Interface representing an instance. All values (numeric, date, nominal,
#  * string or relational) are internally stored as floating-point numbers in the
#  * original concrete class implementations (now called DenseInstance.java and
#  * SparseInstance.java), and the methods in this interface reflect this. If an
#  * attribute is nominal (or a string or relational), the stored value is the
#  * index of the corresponding nominal (or string or relational) value in the
#  * attribute's definition. We have chosen this approach in favor of a more
#  * elegant object-oriented approach because it is much faster.
#  * <p>
#  *
#  * Typical usage (code from the main() method of this class):
#  * <p>
#  *
#  * <code>
#  * ... <br>
#  *
#  * // Create empty instance with three attribute values <br>
#  * Instance inst = new DenseInstance(3); <br><br>
#  *
#  * // Set instance's values for the attributes "length", "weight", and "position"<br>
#  * inst.setValue(length, 5.3); <br>
#  * inst.setValue(weight, 300); <br>
#  * inst.setValue(position, "first"); <br><br>
#  *
#  * // Set instance's dataset to be the dataset "race" <br>
#  * inst.setDataset(race); <br><br>
#  *
#  * // Print the instance <br>
#  * System.out.println("The instance: " + inst); <br>
#  *
#  * ... <br>
#  * </code>
#  * <p>
#  *
#  * All methods that change an instance's attribute values must be safe, ie. a
#  * change of an instance's attribute values must not affect any other instances.
#  *
#  * @author Eibe Frank (eibe@cs.waikato.ac.nz)
#  * @version $Revision: 15069 $
#  */
# public interface Instance extends Copyable {
#
#   /**
#    * Returns the attribute with the given index.
#    *
#    * @param index the attribute's index
#    * @return the attribute at the given position
#    * @throws UnassignedDatasetException if instance doesn't have access to a
#    *           dataset
#    */
#   public Attribute attribute(int index);
#
#   /**
#    * Returns the attribute with the given index in the sparse representation.
#    * Same as attribute(int) for a DenseInstance.
#    *
#    * @param indexOfIndex the index of the attribute's index
#    * @return the attribute at the given position
#    * @throws UnassignedDatasetException if instance doesn't have access to a
#    *           dataset
#    */
#   public Attribute attributeSparse(int indexOfIndex);
#
#   /**
#    * Returns class attribute.
#    *
#    * @return the class attribute
#    * @throws UnassignedDatasetException if the class is not set or the instance
#    *           doesn't have access to a dataset
#    */
#   public Attribute classAttribute();
#
#   /**
#    * Returns the class attribute's index.
#    *
#    * @return the class index as an integer
#    * @throws UnassignedDatasetException if instance doesn't have access to a
#    *           dataset
#    */
#   public int classIndex();
#
#   /**
#    * Tests if an instance's class is missing.
#    *
#    * @return true if the instance's class is missing
#    * @throws UnassignedClassException if the class is not set or the instance
#    *           doesn't have access to a dataset
#    */
#   public boolean classIsMissing();
#
#   /**
#    * Returns an instance's class value as a floating-point number.
#    *
#    * @return the corresponding value as a double (If the corresponding attribute
#    *         is nominal (or a string) then it returns the value's index as a
#    *         double).
#    * @throws UnassignedClassException if the class is not set or the instance
#    *           doesn't have access to a dataset
#    */
#   public double classValue();
#
#   /**
#    * Copies the instance but fills up its values based on the given array
#    * of doubles. The copy has access to the same dataset.
#    *
#    * @param values the array with new values
#    * @return the new instance
#    */
#   public Instance copy(double[] values);
#
#   /**
#    * Returns the dataset this instance has access to. (ie. obtains information
#    * about attribute types from) Null if the instance doesn't have access to a
#    * dataset.
#    *
#    * @return the dataset the instance has accesss to
#    */
#   public Instances dataset();
#
#   /**
#    * Deletes an attribute at the given position (0 to numAttributes() - 1). Only
#    * succeeds if the instance does not have access to any dataset because
#    * otherwise inconsistencies could be introduced.
#    *
#    * @param position the attribute's position
#    * @throws RuntimeException if the instance has access to a dataset
#    */
#   public void deleteAttributeAt(int position);
#
#   /**
#    * Returns an enumeration of all the attributes.
#    *
#    * @return enumeration of all the attributes
#    * @throws UnassignedDatasetException if the instance doesn't have access to a
#    *           dataset
#    */
#   public Enumeration<Attribute> enumerateAttributes();
#
#   /**
#    * Tests if the headers of two instances are equivalent.
#    *
#    * @param inst another instance
#    * @return true if the header of the given instance is equivalent to this
#    *         instance's header
#    * @throws UnassignedDatasetException if instance doesn't have access to any
#    *           dataset
#    */
#   public boolean equalHeaders(Instance inst);
#
#   /**
#    * Checks if the headers of two instances are equivalent. If not, then returns
#    * a message why they differ.
#    *
#    * @param inst another instance
#    * @return null if the header of the given instance is equivalent to this
#    *         instance's header, otherwise a message with details on why they
#    *         differ
#    */
#   public String equalHeadersMsg(Instance inst);
#
#   /**
#    * Tests whether an instance has a missing value. Skips the class attribute if
#    * set.
#    *
#    * @return true if instance has a missing value.
#    * @throws UnassignedDatasetException if instance doesn't have access to any
#    *           dataset
#    */
#   public boolean hasMissingValue();
#
#   /**
#    * Returns the index of the attribute stored at the given position in the
#    * sparse representation. Identify function for an instance of type
#    * DenseInstance.
#    *
#    * @param position the position
#    * @return the index of the attribute stored at the given position
#    */
#   public int index(int position);
#
#   /**
#    * Inserts an attribute at the given position (0 to numAttributes()). Only
#    * succeeds if the instance does not have access to any dataset because
#    * otherwise inconsistencies could be introduced.
#    *
#    * @param position the attribute's position
#    * @throws RuntimeException if the instance has accesss to a dataset
#    * @throws IllegalArgumentException if the position is out of range
#    */
#   public void insertAttributeAt(int position);
#
#   /**
#    * Tests if a specific value is "missing".
#    *
#    * @param attIndex the attribute's index
#    * @return true if the value is "missing"
#    */
#   public boolean isMissing(int attIndex);
#
#   /**
#    * Tests if a specific value is "missing" in the sparse representation. Samse
#    * as isMissing(int) for a DenseInstance.
#    *
#    * @param indexOfIndex the index of the attribute's index
#    * @return true if the value is "missing"
#    */
#   public boolean isMissingSparse(int indexOfIndex);
#
#   /**
#    * Tests if a specific value is "missing". The given attribute has to belong
#    * to a dataset.
#    *
#    * @param att the attribute
#    * @return true if the value is "missing"
#    */
#   public boolean isMissing(Attribute att);
#
#   /**
#    * Merges this instance with the given instance and returns the result.
#    * Dataset is set to null. The returned instance is of the same type as this
#    * instance.
#    *
#    * @param inst the instance to be merged with this one
#    * @return the merged instances
#    */
#   public Instance mergeInstance(Instance inst);
#
#   /**
#    * Returns the number of attributes.
#    *
#    * @return the number of attributes as an integer
#    */
#   public int numAttributes();
#
#   /**
#    * Returns the number of class labels.
#    *
#    * @return the number of class labels as an integer if the class attribute is
#    *         nominal, 1 otherwise.
#    * @throws UnassignedDatasetException if instance doesn't have access to any
#    *           dataset
#    */
#   public int numClasses();
#
#   /**
#    * Returns the number of values present in a sparse representation.
#    *
#    * @return the number of values
#    */
#   public int numValues();
#
#   /**
#    * Replaces all missing values in the instance with the values contained in
#    * the given array. A deep copy of the vector of attribute values is performed
#    * before the values are replaced.
#    *
#    * @param array containing the means and modes
#    * @throws IllegalArgumentException if numbers of attributes are unequal
#    */
#   public void replaceMissingValues(double[] array);
#
#   /**
#    * Sets the class value of an instance to be "missing". A deep copy of the
#    * vector of attribute values is performed before the value is set to be
#    * missing.
#    *
#    * @throws UnassignedClassException if the class is not set
#    * @throws UnassignedDatasetException if the instance doesn't have access to a
#    *           dataset
#    */
#   public void setClassMissing();
#
#   /**
#    * Sets the class value of an instance to the given value (internal
#    * floating-point format). A deep copy of the vector of attribute values is
#    * performed before the value is set.
#    *
#    * @param value the new attribute value (If the corresponding attribute is
#    *          nominal (or a string) then this is the new value's index as a
#    *          double).
#    * @throws UnassignedClassException if the class is not set
#    * @throws UnassignedDatasetException if the instance doesn't have access to a
#    *           dataset
#    */
#   public void setClassValue(double value);
#
#   /**
#    * Sets the class value of an instance to the given value. A deep copy of the
#    * vector of attribute values is performed before the value is set.
#    *
#    * @param value the new class value (If the class is a string attribute and
#    *          the value can't be found, the value is added to the attribute).
#    * @throws UnassignedClassException if the class is not set
#    * @throws UnassignedDatasetException if the dataset is not set
#    * @throws IllegalArgumentException if the attribute is not nominal or a
#    *           string, or the value couldn't be found for a nominal attribute
#    */
#   public void setClassValue(String value);
#
#   /**
#    * Sets the reference to the dataset. Does not check if the instance is
#    * compatible with the dataset. Note: the dataset does not know about this
#    * instance. If the structure of the dataset's header gets changed, this
#    * instance will not be adjusted automatically.
#    *
#    * @param instances the reference to the dataset
#    */
#   public void setDataset(Instances instances);
#
#   /**
#    * Sets a specific value to be "missing". Performs a deep copy of the vector
#    * of attribute values before the value is set to be missing.
#    *
#    * @param attIndex the attribute's index
#    */
#   public void setMissing(int attIndex);
#
#   /**
#    * Sets a specific value to be "missing". Performs a deep copy of the vector
#    * of attribute values before the value is set to be missing. The given
#    * attribute has to belong to a dataset.
#    *
#    * @param att the attribute
#    */
#   public void setMissing(Attribute att);
#
#   /**
#    * Sets a specific value in the instance to the given value (internal
#    * floating-point format). Performs a deep copy of the vector of attribute
#    * values before the value is set.
#    *
#    * @param attIndex the attribute's index
#    * @param value the new attribute value (If the corresponding attribute is
#    *          nominal (or a string) then this is the new value's index as a
#    *          double).
#    */
#   public void setValue(int attIndex, double value);
#
#   /**
#    * Sets a specific value in the instance to the given value (internal
#    * floating-point format), given an index into the sparse representation.
#    * Performs a deep copy of the vector of attribute values before the value is
#    * set. Same as setValue(int, double) for a DenseInstance.
#    *
#    * @param indexOfIndex the index of the attribute's index
#    * @param value the new attribute value (If the corresponding attribute is
#    *          nominal (or a string) then this is the new value's index as a
#    *          double).
#    */
#   public void setValueSparse(int indexOfIndex, double value);
#
#   /**
#    * Sets a value of a nominal or string attribute to the given value. Performs
#    * a deep copy of the vector of attribute values before the value is set.
#    *
#    * @param attIndex the attribute's index
#    * @param value the new attribute value (If the attribute is a string
#    *          attribute and the value can't be found, the value is added to the
#    *          attribute).
#    * @throws UnassignedDatasetException if the dataset is not set
#    * @throws IllegalArgumentException if the selected attribute is not nominal
#    *           or a string, or the supplied value couldn't be found for a
#    *           nominal attribute
#    */
#   public void setValue(int attIndex, String value);
#
#   /**
#    * Sets a specific value in the instance to the given value (internal
#    * floating-point format). Performs a deep copy of the vector of attribute
#    * values before the value is set, so if you are planning on calling setValue
#    * many times it may be faster to create a new instance using toDoubleArray.
#    * The given attribute has to belong to a dataset.
#    *
#    * @param att the attribute
#    * @param value the new attribute value (If the corresponding attribute is
#    *          nominal (or a string) then this is the new value's index as a
#    *          double).
#    */
#   public void setValue(Attribute att, double value);
#
#   /**
#    * Sets a value of an nominal or string attribute to the given value. Performs
#    * a deep copy of the vector of attribute values before the value is set, so
#    * if you are planning on calling setValue many times it may be faster to
#    * create a new instance using toDoubleArray. The given attribute has to
#    * belong to a dataset.
#    *
#    * @param att the attribute
#    * @param value the new attribute value (If the attribute is a string
#    *          attribute and the value can't be found, the value is added to the
#    *          attribute).
#    * @throws IllegalArgumentException if the the attribute is not nominal or a
#    *           string, or the value couldn't be found for a nominal attribute
#    */
#   public void setValue(Attribute att, String value);
#
#   /**
#    * Sets the weight of an instance.
#    *
#    * @param weight the weight
#    */
#   public void setWeight(double weight);
#
#   /**
#    * Returns the relational value of a relational attribute.
#    *
#    * @param attIndex the attribute's index
#    * @return the corresponding relation as an Instances object
#    * @throws IllegalArgumentException if the attribute is not a relation-valued
#    *           attribute
#    * @throws UnassignedDatasetException if the instance doesn't belong to a
#    *           dataset.
#    */
#   public Instances relationalValue(int attIndex);
#
#   /**
#    * Returns the relational value of a relational attribute.
#    *
#    * @param att the attribute
#    * @return the corresponding relation as an Instances object
#    * @throws IllegalArgumentException if the attribute is not a relation-valued
#    *           attribute
#    * @throws UnassignedDatasetException if the instance doesn't belong to a
#    *           dataset.
#    */
#   public Instances relationalValue(Attribute att);
#
#   /**
#    * Returns the value of a nominal, string, date, or relational attribute for
#    * the instance as a string.
#    *
#    * @param attIndex the attribute's index
#    * @return the value as a string
#    * @throws IllegalArgumentException if the attribute is not a nominal, string,
#    *           date, or relation-valued attribute.
#    * @throws UnassignedDatasetException if the instance doesn't belong to a
#    *           dataset.
#    */
#   public String stringValue(int attIndex);
#
#   /**
#    * Returns the value of a nominal, string, date, or relational attribute for
#    * the instance as a string.
#    *
#    * @param att the attribute
#    * @return the value as a string
#    * @throws IllegalArgumentException if the attribute is not a nominal, string,
#    *           date, or relation-valued attribute.
#    * @throws UnassignedDatasetException if the instance doesn't belong to a
#    *           dataset.
#    */
#   public String stringValue(Attribute att);
#
#   /**
#    * Returns the values of each attribute as an array of doubles. Creates a fresh array object for this.
#    *
#    * @return an array containing all the instance attribute values
#    */
#   public double[] toDoubleArray();
#
#   /**
#    * Returns the description of one instance (without weight appended). If the
#    * instance doesn't have access to a dataset, it returns the internal
#    * floating-point values. Quotes string values that contain whitespace
#    * characters.
#    *
#    * This method is used by getRandomNumberGenerator() in Instances.java in
#    * order to maintain backwards compatibility with weka 3.4.
#    *
#    * @param afterDecimalPoint maximum number of digits after the decimal point
#    *          for numeric values
#    *
#    * @return the instance's description as a string
#    */
#   public String toStringNoWeight(int afterDecimalPoint);
#
#   /**
#    * Returns the description of one instance (without weight appended). If the
#    * instance doesn't have access to a dataset, it returns the internal
#    * floating-point values. Quotes string values that contain whitespace
#    * characters.
#    *
#    * This method is used by getRandomNumberGenerator() in Instances.java in
#    * order to maintain backwards compatibility with weka 3.4.
#    *
#    * @return the instance's description as a string
#    */
#   public String toStringNoWeight();
#
#   /**
#    * Returns the description of one instance with any numeric values printed at
#    * the supplied maximum number of decimal places. If the instance doesn't have
#    * access to a dataset, it returns the internal floating-point values. Quotes
#    * string values that contain whitespace characters.
#    *
#    * @param afterDecimalPoint the maximum number of digits permitted after the
#    *          decimal point for a numeric value
#    *
#    * @return the instance's description as a string
#    */
#   public String toStringMaxDecimalDigits(int afterDecimalPoint);
#
#   /**
#    * Returns the description of one value of the instance as a string. If the
#    * instance doesn't have access to a dataset, it returns the internal
#    * floating-point value. Quotes string values that contain whitespace
#    * characters, or if they are a question mark.
#    *
#    * @param attIndex the attribute's index
#    * @param afterDecimalPoint the maximum number of digits permitted after the
#    *          decimal point for numeric values
#    * @return the value's description as a string
#    */
#   public String toString(int attIndex, int afterDecimalPoint);
#
#   /**
#    * Returns the description of one value of the instance as a string. If the
#    * instance doesn't have access to a dataset, it returns the internal
#    * floating-point value. Quotes string values that contain whitespace
#    * characters, or if they are a question mark.
#    *
#    * @param attIndex the attribute's index
#    * @return the value's description as a string
#    */
#   public String toString(int attIndex);
#
#   /**
#    * Returns the description of one value of the instance as a string. If the
#    * instance doesn't have access to a dataset it returns the internal
#    * floating-point value. Quotes string values that contain whitespace
#    * characters, or if they are a question mark. The given attribute has to
#    * belong to a dataset.
#    *
#    * @param att the attribute
#    * @param afterDecimalPoint the maximum number of decimal places to print
#    * @return the value's description as a string
#    */
#   public String toString(Attribute att, int afterDecimalPoint);
#
#   /**
#    * Returns the description of one value of the instance as a string. If the
#    * instance doesn't have access to a dataset it returns the internal
#    * floating-point value. Quotes string values that contain whitespace
#    * characters, or if they are a question mark. The given attribute has to
#    * belong to a dataset.
#    *
#    * @param att the attribute
#    * @return the value's description as a string
#    */
#   public String toString(Attribute att);
#
#   /**
#    * Returns an instance's attribute value in internal format.
#    *
#    * @param attIndex the attribute's index
#    * @return the specified value as a double (If the corresponding attribute is
#    *         nominal (or a string) then it returns the value's index as a
#    *         double).
#    */
#   public double value(int attIndex);
#
#   /**
#    * Returns an instance's attribute value in internal format, given an index in
#    * the sparse representation. Same as value(int) for a DenseInstance.
#    *
#    * @param indexOfIndex the index of the attribute's index
#    * @return the specified value as a double (If the corresponding attribute is
#    *         nominal (or a string) then it returns the value's index as a
#    *         double).
#    */
#   public double valueSparse(int indexOfIndex);
#
#   /**
#    * Returns an instance's attribute value in internal format. The given
#    * attribute has to belong to a dataset.
#    *
#    * @param att the attribute
#    * @return the specified value as a double (If the corresponding attribute is
#    *         nominal (or a string) then it returns the value's index as a
#    *         double).
#    */
#   public double value(Attribute att);
#
#   /**
#    * Returns the instance's weight.
#    *
#    * @return the instance's weight as a double
#    */
#   public double weight();
# }
#
# / *
# * This
# program is free
# software: you
# can
# redistribute
# it and / or modify
#             * it
# under
# the
# terms
# of
# the
# GNU
# General
# Public
# License as published
# by
# * the
# Free
# Software
# Foundation, either
# version
# 3
# of
# the
# License, or
# *(at your option)
# any
# later
# version.
# *
# * This
# program is distributed in the
# hope
# that
# it
# will
# be
# useful,
# *but
# WITHOUT
# ANY
# WARRANTY;
# without
# even
# the
# implied
# warranty
# of
# * MERCHANTABILITY or FITNESS
# FOR
# A
# PARTICULAR
# PURPOSE.See
# the
# * GNU
# General
# Public
# License
# for more details.
#          *
#          * You should have received a copy of the GNU General Public License
# * along with this program.If not, see < http://
#     www.gnu.org / licenses / >.
# * /
#
# / *
# * Attribute.java
#   * Copyright(C)
# 1999 - 2012
# University
# of
# Waikato, Hamilton, New
# Zealand
# *
# * /
#
# package
# weka.core;
#
# import java.io.Serializable;
# import java.text.ParseException;
# import java.util.ArrayList;
# import java.util.Date;
# import java.util.Enumeration;
# import java.util.Hashtable;
# import java.util.List;
# import java.util.Properties;
#
# / **
# *Class
# for handling an attribute.Once an attribute has been created, it can't
# * be changed.
# * < p >
# *
# * The following attribute types are supported:
#     * <
#     ul >
# * < li > numeric: < br / >
# *This
# type of attribute
# represents
# a
# floating - point
# number. < / li >
# * < li > nominal: < br / >
# *This
# type of attribute
# represents
# a
# fixed
# set
# of
# nominal
# values. < / li >
# * < li > string: < br / >
# *This
# type of attribute
# represents
# a
# dynamically
# expanding
# set
# of
# nominal
# * values.Usually
# used in text
# classification. < / li >
# * < li > date: < br / >
# *This
# type of attribute
# represents
# a
# date, internally
# represented as
# *floating - point
# number
# storing
# the
# milliseconds
# since
# January
# 1, 1970,
# *00: 00:00
# GMT.The
# string
# representation
# of
# the
# date
# must
# be < a
# * href = "http://www.iso.org/iso/en/prods-services/popstds/datesandtime.html"
#          * target = "_blank" > ISO - 8601 < / a > compliant, the
# default is
# * < code > yyyy - MM - dd
# 'T'
# HH: mm:ss < / code >.< / li >
# * < li > relational: < br / >
# *This
# type of attribute
# can
# contain
# other
# attributes and is, e.g., used
# for
# *representing Multi - Instance data.(Multi-Instance data consists of a nominal
# *attribute
# containing
# the
# bag - id, then
# a
# relational
# attribute
# with all the
# *attributes
# of
# the
# bag, and finally the
#
#
# class attribute.) < / li >
# * < / ul >
# *
# * Typical usage (code from the main() method of this class ):
#     * <
#
#
#     p >
# *
# * < code >
# *... < br >
# *
# * // Create
# numeric
# attributes
# "length" and "weight" < br >
# *Attribute
# length = new
# Attribute("length"); < br >
# *Attribute
# weight = new
# Attribute("weight"); < br > < br >
# *
# * // Create
# list
# to
# hold
# nominal
# values
# "first", "second", "third" < br >
# *List < String > my_nominal_values = new
# ArrayList < String > (3); < br >
# *my_nominal_values.add("first"); < br >
# *my_nominal_values.add("second"); < br >
# *my_nominal_values.add("third"); < br > < br >
# *
# * // Create
# nominal
# attribute
# "position" < br >
# *Attribute
# position = new
# Attribute("position", my_nominal_values); < br >
# *
# * ... < br >
# * < / code >
# * < p >
# *
# *
#
# @author
#
#
# Eibe
# Frank(eibe @ cs.waikato.ac.nz)
# * @ version $Revision: 14509 $
# * /
# public
#
#
# class Attribute implements Copyable, Serializable, RevisionHandler {
#
# / ** for serialization * /
# static final long serialVersionUID = -742180568732916383L;
#
# / ** Constant set for numeric attributes.* /
# public static final int NUMERIC = 0;
#
# / ** Constant set for nominal attributes.* /
# public static final int NOMINAL = 1;
#
# / ** Constant set for attributes with string values.* /
# public static final int STRING = 2;
#
# / ** Constant set for attributes with date values.* /
# public static final int DATE = 3;
#
# / ** Constant set for relation-valued attributes.* /
# public static final int RELATIONAL = 4;
#
# / ** Constant set for symbolic attributes.* /
# public static final int ORDERING_SYMBOLIC = 0;
#
# / ** Constant set for ordered attributes.* /
# public static final int ORDERING_ORDERED = 1;
#
# / ** Constant set for modulo-ordered attributes.* /
# public static final int ORDERING_MODULO = 2;
#
# / ** The keyword used to denote the start of an arff attribute declaration * /
# public final static String ARFF_ATTRIBUTE = "@attribute";
#
# / ** A keyword used to denote a numeric attribute * /
# public final static String ARFF_ATTRIBUTE_INTEGER = "integer";
#
# / ** A keyword used to denote a numeric attribute * /
# public final static String ARFF_ATTRIBUTE_REAL = "real";
#
# / ** A keyword used to denote a numeric attribute * /
# public final static String ARFF_ATTRIBUTE_NUMERIC = "numeric";
#
# / ** The keyword used to denote a string attribute * /
# public final static String ARFF_ATTRIBUTE_STRING = "string";
#
# / ** The keyword used to denote a date attribute * /
# public final static String ARFF_ATTRIBUTE_DATE = "date";
#
# / ** The keyword used to denote a relation-valued attribute * /
# public final static String ARFF_ATTRIBUTE_RELATIONAL = "relational";
#
# / ** The keyword used to denote the end of the declaration of a subrelation * /
# public final static String ARFF_END_SUBRELATION = "@end";
#
# / ** Strings longer than this will be stored compressed.* /
# protected static final int STRING_COMPRESS_THRESHOLD = 200;
#
# / ** The attribute's name. */
# protected final / * @ spec_public non_null @ * / String m_Name;
#
# / ** The attribute's type. */
# protected / * @ spec_public @ * / int m_Type;
# / *
# * @ invariant m_Type == NUMERIC | | m_Type == DATE | | m_Type == STRING | |
# * m_Type == NOMINAL | | m_Type == RELATIONAL;
# * /
#
# / ** The attribute info (null for numeric attributes) * /
# protected AttributeInfo m_AttributeInfo;
#
# / ** The attribute's index. */
# protected / * @ spec_public @ * / int m_Index = -1;
#
# / ** The attribute's weight. */
# protected double m_Weight = 1.0;
#
# / ** The meta data for the attribute.* /
# protected AttributeMetaInfo m_AttributeMetaInfo;
#
# / **
# * Constructor for a numeric attribute.
# *
# * @ param attributeName the name for the attribute
# * /
# // @ requires attributeName != null;
# // @ ensures m_Name == attributeName;
# public Attribute(String attributeName) {
#
# this(attributeName, (ProtectedProperties)null);
# }
#
# / **
# * Constructor for a numeric attribute, where metadata is supplied.
# *
# * @ param attributeName the name for the attribute
# * @ param metadata the attribute's properties
# * /
# // @ requires attributeName != null;
# // @ requires metadata != null;
# // @ ensures m_Name == attributeName;
# public Attribute(String attributeName, ProtectedProperties metadata) {
#
# m_Name = attributeName;
# if (metadata != null) {
# m_AttributeMetaInfo = new AttributeMetaInfo(metadata, this);
# }
# }
#
# / **
# * Constructor for a numeric or string attribute.Provides an alternative
# * way for creating string attributes.
# *
# * @ param attributeName the name for the attribute
# * @ param createStringAttribute if true, a string attribute will be created, otherwise a numeric one.
# * /
# // @ requires attributeName != null;
# // @ ensures m_Name == attributeName;
# public Attribute(String attributeName, boolean createStringAttribute) {
#
# this(attributeName, createStringAttribute, (ProtectedProperties)null);
# }
#
# / **
# * Constructor for a numeric or string attribute, where metadata is supplied.Provides an alternative
# * way for creating string attributes.
# *
# * @ param attributeName the name for the attribute
# * @ param createStringAttribute if true, a string attribute will be created, otherwise a numeric one.
# * @ param metadata the attribute's properties
# * /
# // @ requires attributeName != null;
# // @ requires metadata != null;
# // @ ensures m_Name == attributeName;
# public Attribute(String attributeName, boolean createStringAttribute, ProtectedProperties metadata) {
#
# m_Name = attributeName;
# if (createStringAttribute) {
# m_AttributeInfo = new NominalAttributeInfo((List < String > )null, attributeName);
# m_Type = STRING;
# }
# if (metadata != null) {
# m_AttributeMetaInfo = new AttributeMetaInfo(metadata, this);
# }
# }
#
# / **
# * Constructor for a date attribute.
# *
# * @ param attributeName the name for the attribute
# * @ param dateFormat a string suitable for use with SimpleDateFormatter for
# * parsing dates.
# * /
# // @ requires attributeName != null;
# // @ requires dateFormat != null;
# // @ ensures m_Name == attributeName;
# public Attribute(String attributeName, String dateFormat) {
#
# this(attributeName, dateFormat, (ProtectedProperties)null);
# }
#
# / **
# * Constructor for a date attribute, where metadata is supplied.
# *
# * @ param attributeName the name for the attribute
# * @ param dateFormat a string suitable for use with SimpleDateFormatter for
# * parsing dates.
# * @ param metadata the attribute's properties
# * /
# // @ requires attributeName != null;
# // @ requires dateFormat != null;
# // @ requires metadata != null;
# // @ ensures m_Name == attributeName;
# public Attribute(String attributeName, String dateFormat,
# ProtectedProperties metadata) {
#
# m_Name = attributeName;
# m_Type = DATE;
# m_AttributeInfo = new DateAttributeInfo(dateFormat);
# if (metadata != null) {
# m_AttributeMetaInfo = new AttributeMetaInfo(metadata, this);
# }
# }
#
# / **
# * Constructor for nominal attributes and string attributes.If a null vector
# * of attribute values is passed to the method, the attribute is assumed to be
# * a string.
# *
# * @ param attributeName the name for the attribute
# * @ param attributeValues a vector of strings denoting the attribute values.
# * Null if the attribute is a string attribute.
# * /
# // @ requires attributeName != null;
# // @ ensures m_Name == attributeName;
# public Attribute(String attributeName, List < String > attributeValues) {
#
# this(attributeName, attributeValues, (ProtectedProperties)null);
# }
#
# / **
# * Constructor for nominal attributes and string attributes, where metadata is
# * supplied.If a null vector of attribute values is passed to the method, the
# * attribute is assumed to be a string.
# *
# * @ param attributeName the name for the attribute
# * @ param attributeValues a vector of strings denoting the attribute values.
# * Null if the attribute is a string attribute.
# * @ param metadata the attribute's properties
# * /
# // @ requires attributeName != null;
# // @ requires metadata != null;
# / *
# * @ ensures m_Name == attributeName; ensures m_Index == -1; ensures
# * attributeValues == null & & m_Type == STRING | | attributeValues != null & &
# * m_Type == NOMINAL & & m_Values.size() == attributeValues.size(); signals
# * (IllegalArgumentException ex) ( * if duplicate strings in attributeValues
# * * );
# * /
# public Attribute(String attributeName, List < String > attributeValues,
# ProtectedProperties metadata) {
#
# m_Name = attributeName;
# m_AttributeInfo = new NominalAttributeInfo(attributeValues, attributeName);
# if (attributeValues == null) {
# m_Type = STRING;
# } else {
# m_Type = NOMINAL;
# }
# if (metadata != null) {
# m_AttributeMetaInfo = new AttributeMetaInfo(metadata, this);
# }
# }
#
# / **
# * Constructor for relation-valued attributes.
# *
# * @ param attributeName the name for the attribute
# * @ param header an Instances object specifying the header of the relation.
# * /
# public Attribute(String attributeName, Instances header) {
#
# this(attributeName, header, (ProtectedProperties)null);
# }
#
# / **
# * Constructor for relation-valued attributes.
# *
# * @ param attributeName the name for the attribute
# * @ param header an Instances object specifying the header of the relation.
# * @ param metadata the attribute's properties
# * /
# public Attribute(String attributeName, Instances header,
# ProtectedProperties metadata) {
#
# if (header.numInstances() > 0) {
# throw new IllegalArgumentException("Header for relation-valued "
# + "attribute should not contain " + "any instances");
# }
# m_Name = attributeName;
# m_Type = RELATIONAL;
# m_AttributeInfo = new RelationalAttributeInfo(header);
# if (metadata != null) {
# m_AttributeMetaInfo = new AttributeMetaInfo(metadata, this);
# }
# }
#
# / **
# * Produces a shallow copy of this attribute.
# *
# * @
#
#
# return a
# copy
# of
# this
# attribute
# with the same index
# * /
# //
#
# @also
#
#
# ensures \result
# instanceof
# Attribute;
#
#
# @Override
#
#
# public / * @ pure
# non_null @ * / Object
# copy()
# {
#
# return copy(m_Name);
# }
#
# / **
# *Returns
# an
# enumeration
# of
# all
# the
# attribute
# 's values if the attribute is
# * nominal, string, or relation - valued, null
# otherwise.
# *
# * @
# return enumeration
# of
# all
# the
# attribute
# 's values
# * /
# public
# final / * @ pure @ * / Enumeration < Object > enumerateValues()
# {
#
# if (isNominal() | | isString())
# {
#     final
# Enumeration < Object > ee =
# new
# WekaEnumeration < Object > (((NominalAttributeInfo)m_AttributeInfo).m_Values);
# return new
# Enumeration < Object > ()
# {
# @ Override
# public
# boolean
# hasMoreElements()
# {
# return ee.hasMoreElements();
# }
#
# @Override
#
#
# public
# Object
# nextElement()
# {
# Object
# oo = ee.nextElement();
# if (oo instanceof SerializedObject) {
# return ((SerializedObject) oo).getObject();
# } else {
# return oo;
# }
# }
# };
# }
# return null;
# }
#
# / **
# *Tests if given
# attribute is equal
# to
# this
# attribute.Attribute
# indices
# are
# ignored in the
# comparison.
# *
# * @ param
# other
# the
# Object
# to
# be
# compared
# to
# this
# attribute
# * @
# return true if the
# given
# attribute is equal
# to
# this
# attribute
# * /
#
# @Override
#
#
# public
# final / * @ pure @ * / boolean
# equals(Object
# other) {
# return (equalsMsg(other) == null);
# }
#
# / **
# *Returns
# a
# hash
# code
# for this attribute based on its name.
# *
# * @
# return the
# hash
# code
# * /
#
# @Override
#
#
# public
# final / * @ pure @ * / int
# hashCode()
# {
# return name().hashCode();
# }
#
# / **
# *Tests if given
# attribute is equal
# to
# this
# attribute.If
# they
# 're not the
# * same
# a
# message
# detailing
# why
# they
# differ
# will
# be
# returned, otherwise
# null.
# * Attribute
# indices
# are
# ignored in the
# comparison.
# *
# * @ param
# other
# the
# Object
# to
# be
# compared
# to
# this
# attribute
# * @
# return null if the
# given
# attribute is equal
# to
# this
# attribute
# * /
# public
# final
# String
# equalsMsg(Object
# other) {
# if (other == null)
# {
# return "Comparing with null object";
# }
#
# if (!(other.getClass().equals(this.getClass()))) {
# return "Object has wrong class";
# }
#
# Attribute
# att = (Attribute)
# other;
# if (!m_Name.equals(att.m_Name)) {
# return "Names differ: " + m_Name + " != " + att.m_Name;
# }
#
# if (isNominal() & & att.isNominal()) {
# if (((NominalAttributeInfo)m_AttributeInfo).m_Values.size() !=
#         ((NominalAttributeInfo)att.m_AttributeInfo).m_Values.size()) {
# return "Different number of labels: " + ((NominalAttributeInfo)
#     m_AttributeInfo).m_Values.size() + " != "
# + ((NominalAttributeInfo)att.m_AttributeInfo).m_Values.size();
# }
#
# for (int
# i = 0; i < ((NominalAttributeInfo)m_AttributeInfo).m_Values.size(); i++) {
# if (!((NominalAttributeInfo)m_AttributeInfo).m_Values.get(i).
# equals(((NominalAttributeInfo)att.m_AttributeInfo).m_Values.get(i))) {
# return "Labels differ at position " + (i + 1) + ": "
# + ((NominalAttributeInfo)m_AttributeInfo).m_Values.get(i) + " != " +
# ((NominalAttributeInfo)att.m_AttributeInfo).m_Values.get(i);
# }
# }
#
# return null;
# }
#
# if (isRelationValued() & & att.isRelationValued()) {
# return ((RelationalAttributeInfo)m_AttributeInfo).m_Header.equalHeadersMsg(
#     ((RelationalAttributeInfo)att.m_AttributeInfo).m_Header);
# }
#
# if ((type() != att.type())) {
# return "Types differ: " + typeToString(this) + " != " + typeToString(att);
# }
#
# return null;
# }
#
# / **
# *Returns
# a
# string
# representation
# of
# the
# attribute
# type.
# *
# * @ param
# att
# the
# attribute
# to
# return the
# type string
# for
#     * @ return the
#     string
#     representation
#     of
#     the
#     attribute
#     type
#     * /
#     public
#     static
#     String
#     typeToString(Attribute
#     att) {
#     return typeToString(att.type());
#     }
#
#     / **
#     *Returns
#     a
#     string
#     representation
#     of
#     the
#     attribute
#     type.
#     *
#     * @ param
#     type the type
#     of
#     the
#     attribute
#     * @
#     return the
#     string
#     representation
#     of
#     the
#     attribute
#     type
#     * /
#     public
#     static
#     String
#     typeToString(int
#     type) {
#         String
#     result;
#
#     switch(type)
#     {
#         case
#     NUMERIC: \
#         result = "numeric";
#     break;
#
#     case
#     NOMINAL:
#     result = "nominal";
#     break;
#
# case
# STRING:
# result = "string";
# break;
#
# case
# DATE:
# result = "date";
# break;
#
# case
# RELATIONAL:
# result = "relational";
# break;
#
# default:
# result = "unknown(" + type + ")";
# }
#
# return result;
# }
#
# / **
# *Returns
# a
# short
# string
# representation
# of
# the
# attribute
# type.
# *
# * @ param
# att
# the
# attribute
# to
# return the
# type string
# for
#     * @ return the
#     string
#     representation
#     of
#     the
#     attribute
#     type
#     * /
#     public
#     static
#     String
#     typeToStringShort(Attribute
#     att) {
#     return typeToStringShort(att.type());
#     }
#
#     / **
#     *Returns
#     a
#     short
#     string
#     representation
#     of
#     the
#     attribute
#     type.
#     *
#     * @ param
#     type the type
#     of
#     the
#     attribute
#     * @
#     return the
#     string
#     representation
#     of
#     the
#     attribute
#     type
#     * /
#     public
#     static
#     String
#     typeToStringShort(int
#     type) {
#         String
#     result;
#
#     switch(type)
#     {
#         case
#     NUMERIC: \
#         result = "Num";
#     break;
#
#     case
#     NOMINAL:
#     result = "Nom";
#     break;
#
# case
# STRING:
# result = "Str";
# break;
#
# case
# DATE:
# result = "Dat";
# break;
#
# case
# RELATIONAL:
# result = "Rel";
# break;
#
# default:
# result = "???";
# }
#
# return result;
# }
#
# / **
# *Returns
# the
# index
# of
# this
# attribute.
# *
# * @
# return the
# index
# of
# this
# attribute
# * /
# //
#
# @ensures
#
#  \result == m_Index;
# public
# final / * @ pure @ * / int
# index()
# {
#
# return m_Index;
# }
#
# / **
# *Returns
# the
# index
# of
# a
# given
# attribute
# value.(The
# index
# of
# the
# first
# *occurence
# of
# this
# value.)
# *
# *
#
# @param
#
#
# value
# the
# value
# for which the index is to be returned
# * @
# return the
# index
# of
# the
# given
# attribute
# value if attribute is nominal or a
# *string, -1 if it is not or the
# value
# can
# 't be found
# * /
# public
# final
# int
# indexOfValue(String
# value) {
#
# if (!isNominal() & & !isString()) {
# return -1;
# }
# Object
# store = value;
# if (value.length() > STRING_COMPRESS_THRESHOLD)
# {
# try {
# store = new SerializedObject(value, true);
# } catch (Exception ex) {
# System.err.println("Couldn't compress string attribute value -"
# + " searching uncompressed.");
# }
# }
# Integer
# val = ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.get(store);
# if (val == null)
# {
# return -1;
# } else {
# return val.intValue();
# }
# }
#
# / **
# *Test if the
# attribute is nominal.
# *
# * @
# return true if the
# attribute is nominal
# * /
# //
#
# @ensures
#
#  \result <= = > (m_Type == NOMINAL);
# public
# final / * @ pure @ * / boolean
# isNominal()
# {
#
# return (m_Type == NOMINAL);
# }
#
# / **
# *Tests if the
# attribute is numeric.
# *
# * @
# return true if the
# attribute is numeric
# * /
# //
#
# @ensures
#
#  \result <= = > ((m_Type == NUMERIC) | | (m_Type == DATE));
# public
# final / * @ pure @ * / boolean
# isNumeric()
# {
#
# return ((m_Type == NUMERIC) | | (m_Type == DATE));
# }
#
# / **
# *Tests if the
# attribute is relation
# valued.
# *
# * @
# return true if the
# attribute is relation
# valued
# * /
# //
#
# @ensures
#
#  \result <= = > (m_Type == RELATIONAL);
# public
# final / * @ pure @ * / boolean
# isRelationValued()
# {
#
# return (m_Type == RELATIONAL);
# }
#
# / **
# *Tests if the
# attribute is a
# string.
# *
# * @
# return true if the
# attribute is a
# string
# * /
# //
#
# @ensures
#
#  \result <= = > (m_Type == STRING);
# public
# final / * @ pure @ * / boolean
# isString()
# {
#
# return (m_Type == STRING);
# }
#
# / **
# *Tests if the
# attribute is a
# date
# type.
# *
# * @
# return true if the
# attribute is a
# date
# type
# * /
# //
#
# @ensures
#
#  \result <= = > (m_Type == DATE);
# public
# final / * @ pure @ * / boolean
# isDate()
# {
#
# return (m_Type == DATE);
# }
#
# / **
# *Returns
# the
# attribute
# 's name.
# *
# * @
# return the
# attribute
# 's name as a string
# * /
# //
#
# @ensures
#
#  \result == m_Name;
# public
# final / * @ pure @ * / String
# name()
# {
#
# return m_Name;
# }
#
# / **
# *Returns
# the
# number
# of
# attribute
# values.Returns
# 0
# for attributes that are
# * not either nominal, string, or relation-valued.
# *
# * @
# return the
# number
# of
# attribute
# values
# * /
# public
# final / * @ pure @ * / int
# numValues()
# {
#
# if (!isNominal() & & !isString() & & !isRelationValued()) {
# return 0;
# } else {
# return ((NominalAttributeInfo)m_AttributeInfo).m_Values.size();
# }
# }
#
# / **
# *Returns
# a
# description
# of
# this
# attribute in ARFF
# format.Quotes
# strings if
# *they
# contain
# whitespace
# characters, or if they are a question mark.
# *
# * @
# return a
# description
# of
# this
# attribute as a
# string
# * /
#
# @Override
#
#
# public
# final
# String
# toString()
# {
#
#     StringBuffer
# text = new
# StringBuffer();
#
# text.append(ARFF_ATTRIBUTE).append(" ").append(Utils.quote(m_Name)) \
#     .append(" ");
# switch(m_Type)
# {
#     case
# NOMINAL: \
#     text.append('{');
# Enumeration < Object > enu = enumerateValues();
# while (enu.hasMoreElements()) {
# text.append(Utils.quote((String) enu.nextElement()));
# if (enu.hasMoreElements()) {
# text.append(',');
# }
# }
# text.append('}');
# text.append((weight() != 1.0) ? " {" + weight() + "}": "");
# break;
# case
# NUMERIC:
# text.append(ARFF_ATTRIBUTE_NUMERIC);
# text.append((weight() != 1.0) ?  " {" + weight() + "}": "");
# break;
# case
# STRING:
# text.append(ARFF_ATTRIBUTE_STRING);
# text.append((weight() != 1.0) ?  " {" + weight() + "}": "");
# break;
# case
# DATE:
# text.append(ARFF_ATTRIBUTE_DATE).append(" ")
# .append(
#     Utils.quote(((DateAttributeInfo)m_AttributeInfo).m_DateFormat.toPattern()));
# text.append((weight() != 1.0) ?  " {" + weight() + "}": "");
# break;
# case
# RELATIONAL:
# text.append(ARFF_ATTRIBUTE_RELATIONAL);
# text.append((weight() != 1.0) ?  " {" + weight() + "}": "");
# text.append("\n");
# Enumeration < Attribute > enm = ((RelationalAttributeInfo)
#     m_AttributeInfo).m_Header.enumerateAttributes();
# while (enm.hasMoreElements()) {
# text.append(enm.nextElement()).append("\n");
# }
# text.append(ARFF_END_SUBRELATION).append(" ").append(Utils.quote(m_Name));
# break;
# default:
# text.append("UNKNOWN");
# break;
# }
# return text.toString();
# }
#
# / **
# *Returns
# the
# attribute
# 's type as an integer.
# *
# * @
# return the
# attribute
# 's type.
# * /
# //
#
# @ensures
#
#  \result == m_Type;
# public
# final / * @ pure @ * / int
# type()
# {
#
# return m_Type;
# }
#
# / **
# *Returns
# the
# Date
# format
# pattern in case
# this
# attribute is of
# type DATE,
# *otherwise
# an
# empty
# string.
# *
# * @
# return the
# date
# format
# pattern
# * @ see
# java.text.SimpleDateFormat
# * /
# public
# final
# String
# getDateFormat()
# {
# if (isDate())
# {
# return ((DateAttributeInfo)m_AttributeInfo).m_DateFormat.toPattern();
# } else {
# return "";
# }
# }
#
# / **
# *Returns
# a
# value
# of
# a
# nominal or string
# attribute.Returns
# an
# empty
# string
# * if the
# attribute is neither
# a
# string
# nor
# a
# nominal
# attribute.
# *
# * @ param
# valIndex
# the
# value
# 's index
# * @
# return the
# attribute
# 's value as a string
# * /
# public
# final / * @ non_null
# pure @ * / String
# value(int
# valIndex) {
#
# if (!isNominal() & & !isString()) {
# return "";
# } else {
# Object
# val = ((NominalAttributeInfo)m_AttributeInfo).m_Values.get(valIndex);
#
# // If
# we
# 're storing strings compressed, uncompress it.
# if (val instanceof SerializedObject) {
# val = ((SerializedObject) val).getObject();
# }
# return (String)
# val;
# }
# }
#
# / **
# *Returns
# the
# header
# info
# for a relation - valued attribute, null if the
# * attribute is not relation-valued.
# *
# * @
# return the
# attribute
# 's value as an Instances object
# * /
# public
# final / * @ non_null
# pure @ * / Instances
# relation()
# {
#
# if (!isRelationValued()) {
# return null;
# } else {
# return ((RelationalAttributeInfo)m_AttributeInfo).m_Header;
# }
# }
#
# / **
# *Returns
# a
# value
# of
# a
# relation - valued
# attribute.Returns
# null if the
#         * attribute is not relation - valued.
#         *
#         * @ param
# valIndex
# the
# value
# 's index
# * @
# return the
# attribute
# 's value as an Instances object
# * /
# public
# final / * @ non_null
# pure @ * / Instances
# relation(int
# valIndex) {
#
# if (!isRelationValued()) {
# return null;
# } else {
# return (Instances)((RelationalAttributeInfo)
# m_AttributeInfo).m_Values.get(valIndex);
# }
# }
#
# / **
# *Constructor
# for a numeric attribute with a particular index.
# *
# * @ param attributeName the name for the attribute
# * @ param index the attribute's index
# * /
# // @ requires attributeName != null;
# // @ requires index >= 0;
# // @ ensures m_Name == attributeName;
# // @ ensures m_Index == index;
# public Attribute(String attributeName, int index) {
#
# this(attributeName);
# m_Index = index;
# }
#
# / **
# * Constructor for date attributes with a particular index.
# *
# * @ param attributeName the name for the attribute
# * @ param dateFormat a string suitable for use with SimpleDateFormatter for
# * parsing dates.Null for a default format string.
# * @ param index the attribute's index
# * /
# // @ requires attributeName != null;
# // @ requires index >= 0;
# // @ ensures m_Name == attributeName;
# // @ ensures m_Index == index;
# public Attribute(String attributeName, String dateFormat, int index) {
#
# this(attributeName, dateFormat);
# m_Index = index;
# }
#
# / **
# * Constructor for nominal attributes and string attributes with a particular
# * index.If a null vector of attribute values is passed to the method, the
# * attribute is assumed to be a string.
# *
# * @ param attributeName the name for the attribute
# * @ param attributeValues a vector of strings denoting the attribute values.
# * Null if the attribute is a string attribute.
# * @ param index the attribute's index
# * /
# // @ requires attributeName != null;
# // @ requires index >= 0;
# // @ ensures m_Name == attributeName;
# // @ ensures m_Index == index;
# public Attribute(String attributeName, List < String > attributeValues, int index) {
#
# this(attributeName, attributeValues);
# m_Index = index;
# }
#
# / **
# * Constructor for a relation-valued attribute with a particular index.
# *
# * @ param attributeName the name for the attribute
# * @ param header the header information for this attribute
# * @ param index the attribute's index
# * /
# // @ requires attributeName != null;
# // @ requires index >= 0;
# // @ ensures m_Name == attributeName;
# // @ ensures m_Index == index;
# public Attribute(String attributeName, Instances header, int index) {
#
# this(attributeName, header);
# m_Index = index;
# }
#
# / **
# * Adds a string value to the list of valid strings for attributes of type
# * STRING and returns the index of the string.
# *
# * @ param value The string value to add
# * @
# return the
# index
# assigned
# to
# the
# string, or -1 if the
# attribute is not of
# *type
# Attribute.STRING
# * /
# / *
# * @ requires
# value != null;
# ensures
# isString() & & 0 <= \result & & \result <
# *m_Values.size() | | ! isString() & & \result == -1;
# * /
# public
# int
# addStringValue(String
# value) {
#
# if (!isString()) {
# return -1;
# }
# Object
# store = value;
#
# if (value.length() > STRING_COMPRESS_THRESHOLD)
# {
# try {
# store = new SerializedObject(value, true);
# } catch (Exception ex) {
# System.err.println("Couldn't compress string attribute value -"
# + " storing uncompressed.");
# }
# }
# Integer
# index = ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.get(store);
# if (index != null)
# {
# return index.intValue();
# } else {
# int
# intIndex = ((NominalAttributeInfo)m_AttributeInfo).m_Values.size();
# ((NominalAttributeInfo)m_AttributeInfo).m_Values.add(store);
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.put(store, new
# Integer(intIndex));
# return intIndex;
# }
# }
#
# / **
# *Clear
# the
# map and list
# of
# values and set
# them
# to
# contain
# just
# the
# supplied
# * value
# *
# * @ param
# value
# the
# current( and only) value
# of
# this
# String
# attribute.If
# null
# * then
# just
# the
# map is cleared.
# * /
# public
# void
# setStringValue(String
# value) {
# if (!isString()) {
# return;
# }
#
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.clear();
# ((NominalAttributeInfo)m_AttributeInfo).m_Values.clear();
# if (value != null)
# {
# addStringValue(value);
# }
# }
#
# / **
# *Adds
# a
# string
# value
# to
# the
# list
# of
# valid
# strings
# for attributes of type
# * STRING and returns the index of the string.This method is more efficient
# * than addStringValue(String) for long strings.
# *
# * @ param src The Attribute containing the string value to add.
# * @ param index the index of the string value in the source attribute.
# * @
# return the
# index
# assigned
# to
# the
# string, or -1 if the
# attribute is not of
# *type
# Attribute.STRING
# * /
# / *
# * @ requires
# src != null;
# requires
# 0 <= index & & index < src.m_Values.size();
# *ensures
# isString() & & 0 <= \result & & \result < m_Values.size() | | !
# *isString() & & \result == -1;
# * /
# public
# int
# addStringValue(Attribute
# src, int
# index) {
#
# if (!isString()) {
# return -1;
# }
# Object
# store = ((NominalAttributeInfo)src.m_AttributeInfo).m_Values.get(index);
# Integer
# oldIndex = ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.get(store);
# if (oldIndex != null)
# {
# return oldIndex.intValue();
# } else {
# int
# intIndex = ((NominalAttributeInfo)m_AttributeInfo).m_Values.size();
# ((NominalAttributeInfo)m_AttributeInfo).m_Values.add(store);
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.put(store, new
# Integer(intIndex));
# return intIndex;
# }
# }
#
# / **
# *Adds
# a
# relation
# to
# a
# relation - valued
# attribute.
# *
# * @ param
# value
# The
# value
# to
# add
# * @
# return the
# index
# assigned
# to
# the
# value, or -1 if the
# attribute is not of
# *type
# Attribute.RELATIONAL
# * /
# public
# int
# addRelation(Instances
# value) {
#
# if (!isRelationValued()) {
# return -1;
# }
# if (!((RelationalAttributeInfo)m_AttributeInfo).m_Header.equalHeaders(value)) {
# throw
# new
# IllegalArgumentException("Incompatible value for "
#                          + "relation-valued attribute.\n" + (
#                          (RelationalAttributeInfo)
#                              m_AttributeInfo).m_Header.equalHeadersMsg(value));
# }
# Integer
# index = ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.get(value);
# if (index != null)
# {
# return index.intValue();
# } else {
# int
# intIndex = ((NominalAttributeInfo)m_AttributeInfo).m_Values.size();
# ((NominalAttributeInfo)m_AttributeInfo).m_Values.add(value);
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.put(value, new
# Integer(intIndex));
# return intIndex;
# }
# }
#
# / **
# *Adds
# an
# attribute
# value.Creates
# a
# fresh
# list
# of
# attribute
# values
# before
# * adding
# it.
# *
# * @ param
# value
# the
# attribute
# value
# * /
# final
# void
# addValue(String
# value) {
#
#     ((NominalAttributeInfo)m_AttributeInfo).m_Values =
# Utils.cast(((NominalAttributeInfo)m_AttributeInfo).m_Values.clone());
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable =
# Utils.cast(((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.clone());
# forceAddValue(value);
# }
#
# / **
# *Produces
# a
# shallow
# copy
# of
# this
# attribute
# with a new name.
# *
# * @ param newName the name of the new attribute
# * @
# return a
# copy
# of
# this
# attribute
# with the same index
# * /
# //
#
# @requires
#
#
# newName != null;
# //
#
# @ensures
#
#  \result.m_Name == newName;
# //
#
# @ensures
#
#  \result.m_Index == m_Index;
# //
#
# @ensures
#
#  \result.m_Type == m_Type;
# public
# final / * @ pure
# non_null @ * / Attribute
# copy(String
# newName) {
#
#     Attribute
# copy = new
# Attribute(newName);
#
# copy.m_Index = m_Index;
# copy.m_Type = m_Type;
# copy.m_AttributeInfo = m_AttributeInfo;
# copy.m_AttributeMetaInfo = m_AttributeMetaInfo;
# copy.m_Weight = m_Weight;
#
# return copy;
# }
#
# / **
# *Removes
# a
# value
# of
# a
# nominal, string, or relation - valued
# attribute.Creates
# * a
# fresh
# list
# of
# attribute
# values
# before
# removing
# it.
# *
# * @ param
# index
# the
# value
# 's index
# * @ throws
# IllegalArgumentException if the
# attribute is not of
# the
# correct
# * type
# * /
# // @ requires
# isNominal() | | isString() | | isRelationValued();
# //
#
# @requires
#
#
# 0 <= index & & index < m_Values.size();
# final
# void
# delete(int
# index) {
#
# if (!isNominal() & & !isString() & & !isRelationValued()) {
# throw new IllegalArgumentException("Can only remove value of "
# + "nominal, string or relation-" + " valued attribute!");
# } else {
# ((NominalAttributeInfo)m_AttributeInfo).m_Values =
# Utils.cast(((NominalAttributeInfo)m_AttributeInfo).m_Values.clone());
# ((NominalAttributeInfo)m_AttributeInfo).m_Values.remove(index);
# if (!isRelationValued()) {
# Hashtable < Object, Integer > hash = new Hashtable < Object, Integer > (
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.size());
# Enumeration < Object > enu = ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.keys();
# while (enu.hasMoreElements()) {
# Object string = enu.nextElement();
# Integer valIndexObject = ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.get(string);
# int valIndex = valIndexObject.intValue();
# if (valIndex > index) {
# hash.put(string, new Integer(valIndex - 1));
# } else if (valIndex < index) {
# hash.put(string, valIndexObject);
# }
# }
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable = hash;
# }
# }
# }
#
# / **
# *Adds
# an
# attribute
# value.
# *
# * @ param
# value
# the
# attribute
# value
# * /
# // @ requires
# value != null;
# //
#
# @ensures
#
#
# m_Values.size() == \old(m_Values.size()) + 1;
# final
# void
# forceAddValue(String
# value) {
#
#     Object
# store = value;
# if (value.length() > STRING_COMPRESS_THRESHOLD)
# {
# try {
# store = new SerializedObject(value, true);
# } catch (Exception ex) {
# System.err.println("Couldn't compress string attribute value -"
# + " storing uncompressed.");
# }
# }
# ((NominalAttributeInfo)m_AttributeInfo).m_Values.add(store);
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.
# put(store, new
# Integer(((NominalAttributeInfo)m_AttributeInfo).m_Values.size() - 1));
# }
#
# / **
# *Sets
# the
# index
# of
# this
# attribute.
# *
# * @ param
# index
# the
# index
# of
# this
# attribute
# * /
# // @ requires
# 0 <= index;
# //
#
# @assignable
#
#
# m_Index;
# //
#
# @ensures
#
#
# m_Index == index;
# final
# void
# setIndex(int
# index) {
#
#     m_Index = index;
# }
#
# / **
# *Sets
# a
# value
# of
# a
# nominal
# attribute or string
# attribute.Creates
# a
# fresh
# * list
# of
# attribute
# values
# before
# it is set.
# *
# * @ param
# index
# the
# value
# 's index
# * @ param
# string
# the
# value
# * @ throws
# IllegalArgumentException if the
# attribute is not nominal or string.
# * /
# // @ requires
# string != null;
# //
#
# @requires
#
#
# isNominal() | | isString();
# //
#
# @requires
#
#
# 0 <= index & & index < m_Values.size();
# final
# void
# setValue(int
# index, String
# string) {
#
#     switch(m_Type)
# {
# case
# NOMINAL:
# case
# STRING:
# ((NominalAttributeInfo)m_AttributeInfo).m_Values =
# Utils.cast(((NominalAttributeInfo)m_AttributeInfo).m_Values.clone());
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable =
# Utils.cast(((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.clone());
# Object
# store = string;
# if (string.length() > STRING_COMPRESS_THRESHOLD) {
# try {
# store = new SerializedObject(string, true);
# } catch (Exception ex) {
# System.err.println("Couldn't compress string attribute value -"
# + " storing uncompressed.");
# }
# }
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.
# remove(((NominalAttributeInfo)m_AttributeInfo).m_Values.get(index));
# ((NominalAttributeInfo)m_AttributeInfo).m_Values.set(index, store);
# ((NominalAttributeInfo)m_AttributeInfo).m_Hashtable.put(store, new
# Integer(index));
# break;
# default:
# throw
# new
# IllegalArgumentException("Can only set values for nominal"
#                          + " or string attributes!");
# }
# }
#
# / **
# *Sets
# a
# value
# of
# a
# relation - valued
# attribute.Creates
# a
# fresh
# list
# of
# * attribute
# values
# before
# it is set.
# *
# * @ param
# index
# the
# value
# 's index
# * @ param
# data
# the
# value
# * @ throws
# IllegalArgumentException if the
# attribute is not relation - valued.
# * /
# final
# void
# setValue(int
# index, Instances
# data) {
#
# if (isRelationValued())
# {
# if (!data.equalHeaders(((RelationalAttributeInfo)m_AttributeInfo).m_Header)) {
# throw new IllegalArgumentException("Can't set relational value. "
# + "Headers not compatible.\n" + data.equalHeadersMsg(((RelationalAttributeInfo)m_AttributeInfo).m_Header));
# }
# ((NominalAttributeInfo)m_AttributeInfo).m_Values =
# Utils.cast(((NominalAttributeInfo)m_AttributeInfo).m_Values.clone());
# ((NominalAttributeInfo)m_AttributeInfo).m_Values.set(index, data);
# } else {
# throw
# new
# IllegalArgumentException("Can only set value for"
#                          + " relation-valued attributes!");
# }
# }
#
# / **
# *Returns
# the
# given
# amount
# of
# milliseconds
# formatted
# according
# to
# the
# current
# * Date
# format.
# *
# * @ param
# date
# the
# date, represented in milliseconds
# since
# January
# 1, 1970,
# *00: 00:00
# GMT, to
# return as string
# * @ return the
# formatted
# date
# * /
# //
#
# @requires
#
#
# isDate();
# public / * @ pure @ * / String
# formatDate(double
# date) {
#     switch(m_Type)
# {
#     case
# DATE:
# return ((DateAttributeInfo)m_AttributeInfo).m_DateFormat.format(new
# Date((long)
# date));
# default:
# throw
# new
# IllegalArgumentException("Can only format date values for date"
#                          + " attributes!");
# }
# }
#
# / **
# *Parses
# the
# given
# String as Date, according
# to
# the
# current
# format and
# *returns
# the
# corresponding
# amount
# of
# milliseconds.
# *
# * @ param
# string
# the
# date
# to
# parse
# * @
# return the
# date in milliseconds
# since
# January
# 1, 1970, 00: 00:00
# GMT
# * @ throws
# ParseException if parsing
# fails
# * /
# //
#
# @requires
#
#
# isDate();
# //
#
# @requires
#
#
# string != null;
# public
# double
# parseDate(String
# string) throws
# ParseException
# {
#     switch(m_Type)
# {
#     case
# DATE:
# long
# time = ((DateAttributeInfo)m_AttributeInfo).m_DateFormat.parse(
#     string).getTime();
# // TODO
# put in a
# safety
# check
# here if we
# can
# 't store the value in a
# // double.
# return time;
# default:
# throw
# new
# IllegalArgumentException("Can only parse date values for date"
#                          + " attributes!");
# }
# }
#
# / **
# *Returns
# the
# properties
# supplied
# for this attribute.Returns null
# * if there is no meta data for this attribute.
# *
# * @
# return metadata
# for this attribute
#     * /
# public
# final / * @ pure @ * / ProtectedProperties
# getMetadata()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return null;
# }
# return m_AttributeMetaInfo.m_Metadata;
# }
#
# / **
# *Returns
# the
# ordering
# of
# the
# attribute.One
# of
# the
# following:
# *
# *ORDERING_SYMBOLIC - attribute
# values
# should
# be
# treated as symbols.
#            * ORDERING_ORDERED - attribute
# values
# have
# a
# global ordering.ORDERING_MODULO
#                 * - attribute
# values
# have
# an
# ordering
# which
# wraps.
# *
# * @
# return the
# ordering
# type of the
# attribute
# * /
# public
# final / * @ pure @ * / int
# ordering()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return ORDERING_ORDERED;
# }
# return m_AttributeMetaInfo.m_Ordering;
# }
#
# / **
# *Returns
# whether
# the
# attribute
# values
# are
# equally
# spaced.
# *
# * @
# return whether
# the
# attribute is regular or not
# * /
# public
# final / * @ pure @ * / boolean
# isRegular()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return true;
# }
# return m_AttributeMetaInfo.m_IsRegular;
# }
#
# / **
# *Returns
# whether
# the
# attribute
# can
# be
# averaged
# meaningfully.
# *
# * @
# return whether
# the
# attribute
# can
# be
# averaged or not
# * /
# public
# final / * @ pure @ * / boolean
# isAveragable()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return true;
# }
# return m_AttributeMetaInfo.m_IsAveragable;
# }
#
# / **
# *Returns
# whether
# the
# attribute
# has
# a
# zeropoint and may
# be
# added
# * meaningfully.
# *
# * @
# return whether
# the
# attribute
# has
# a
# zeropoint or not
# * /
# public
# final / * @ pure @ * / boolean
# hasZeropoint()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return true;
# }
# return m_AttributeMetaInfo.m_HasZeropoint;
# }
#
# / **
# *Returns
# the
# attribute
# 's weight.
# *
# * @
# return the
# attribute
# 's weight as a double
# * /
# public
# final / * @ pure @ * / double
# weight()
# {
#
# return m_Weight;
# }
#
# / **
# *Sets
# the
# new
# attribute
# 's weight. Does not modify the weight info stored in the
# * attribute
# 's meta data object!
# *
# * @ param
# value
# the
# new
# weight
# * /
# public
# void
# setWeight(double
# value) {
#
# m_Weight = value;
# }
#
# / **
# *Returns
# the
# lower
# bound
# of
# a
# numeric
# attribute.
# *
# * @
# return the
# lower
# bound
# of
# the
# specified
# numeric
# range
# * /
# public
# final / * @ pure @ * / double
# getLowerNumericBound()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return -Double.MAX_VALUE;
# }
# return m_AttributeMetaInfo.m_LowerBound;
# }
#
# / **
# *Returns
# whether
# the
# lower
# numeric
# bound
# of
# the
# attribute is open.
# *
# * @
# return whether
# the
# lower
# numeric
# bound is open or not (closed)
# * /
# public
# final / * @ pure @ * / boolean
# lowerNumericBoundIsOpen()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return true;
# }
# return m_AttributeMetaInfo.m_LowerBoundIsOpen;
# }
#
# / **
# *Returns
# the
# upper
# bound
# of
# a
# numeric
# attribute.
# *
# * @
# return the
# upper
# bound
# of
# the
# specified
# numeric
# range
# * /
# public
# final / * @ pure @ * / double
# getUpperNumericBound()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return Double.MAX_VALUE;
# }
# return m_AttributeMetaInfo.m_UpperBound;
# }
#
# / **
# *Returns
# whether
# the
# upper
# numeric
# bound
# of
# the
# attribute is open.
# *
# * @
# return whether
# the
# upper
# numeric
# bound is open or not (closed)
# * /
# public
# final / * @ pure @ * / boolean
# upperNumericBoundIsOpen()
# {
#
# if (m_AttributeMetaInfo == null)
# {
# return true;
# }
# return m_AttributeMetaInfo.m_UpperBoundIsOpen;
# }
#
# / **
# *Determines
# whether
# a
# value
# lies
# within
# the
# bounds
# of
# the
# attribute.
# *
# * @ param
# value
# the
# value
# to
# check
# * @
# return whether
# the
# value is in range
# * /
# public
# final / * @ pure @ * / boolean
# isInRange(double
# value) {
#
#        // dates and missing
# values
# are
# a
# special
# case
# if (m_Type == DATE | | Utils.isMissingValue(value))
# {
# return true;
# }
# if (m_Type != NUMERIC) {
# // do
# label
# range
# check
# int
# intVal = (int)
# value;
# if (intVal < 0 | | intVal >= ((NominalAttributeInfo)
# m_AttributeInfo).m_Hashtable.size()) {
# return false;
# }
# } else {
# if (m_AttributeMetaInfo == null)
# {
# return true;
# }
# // do
# numeric
# bounds
# check
# if (m_AttributeMetaInfo.m_LowerBoundIsOpen)
# {
# if (value <= m_AttributeMetaInfo.m_LowerBound) {
# return false;
# }
# } else {
# if (value < m_AttributeMetaInfo.m_LowerBound)
# {
# return false;
# }
# }
# if (m_AttributeMetaInfo.m_UpperBoundIsOpen) {
# if (value >= m_AttributeMetaInfo.m_UpperBound) {
# return false;
# }
# } else {
# if (value > m_AttributeMetaInfo.m_UpperBound)
# {
# return false;
# }
# }
# }
# return true;
# }
#
# / **
# *Returns
# the
# revision
# string.
# *
# * @
# return the
# revision
# * /
#
# @Override
#
#
# public
# String
# getRevision()
# {
# return RevisionUtils.extract("$Revision: 14509 $");
# }
#
# / **
# *Simple
# main
# method
# for testing this
#
#
#     class .
#         *
#         * @ param
#         ops
#         the
#         commandline
#         options
#         * /
#         //
#
#         @requires
#
#         ops != null;
#         //
#
#         @requires
#
#          \nonnullelements(ops);
#         public
#         static
#         void
#         main(String[]
#         ops) {
#
#         try {
#
#         new Attribute("length");
#         Attribute weight = new Attribute("weight");
#
#         // Create date attribute "date"
#         Attribute date = new Attribute("date", "yyyy-MM-dd HH:mm:ss");
#
#         System.out.println(date);
#         double dd = date.parseDate("2001-04-04 14:13:55");
#         System.out.println("Test date = " + dd);
#         System.out.println(date.formatDate(dd));
#
#         dd = new Date().getTime();
#         System.out.println("Date now = " + dd);
#         System.out.println(date.formatDate(dd));
#
#         // Create vector to hold nominal values "first", "second", "third"
#         List < String > my_nominal_values = new ArrayList < String > (3);
#         my_nominal_values.add("first");
#         my_nominal_values.add("second");
#         my_nominal_values.add("third");
#
#         // Create nominal attribute "position"
#         Attribute position = new Attribute("position", my_nominal_values);
#
#         // Print the name of "position"
#         System.out.println("Name of \"position\": " + position.name());
#
#         // Print the values of "position"
#         Enumeration < Object > attValues = position.enumerateValues();
#         while (attValues.hasMoreElements()) {
#         String string = (String) attValues.nextElement();
#         System.out.println("Value of \"position\": " + string);
#         }
#
#         // Shallow
#         copy
#         attribute
#         "position"
#         Attribute
#         copy = (Attribute)
#         position.copy();
#
#         // Test if attributes
#         are
#         the
#         same
#         System.out.println("Copy is the same as original: "
#                            + copy.equals(position));
#
#         // Print
#         index
#         of
#         attribute
#         "weight"(should
#         be
#         unset: -1)
#         System.out.println("Index of attribute \"weight\" (should be -1): "
#                            + weight.index());
#
#         // Print
#         index
#         of
#         value
#         "first"
#         of
#         attribute
#         "position"
#         System.out
#         .println("Index of value \"first\" of \"position\" (should be 0): "
#                  + position.indexOfValue("first"));
#
# // Tests
# type of attribute
# "position"
# System.out.println("\"position\" is numeric: " + position.isNumeric());
# System.out.println("\"position\" is nominal: " + position.isNominal());
# System.out.println("\"position\" is string: " + position.isString());
#
# // Prints
# name
# of
# attribute
# "position"
# System.out.println("Name of \"position\": " + position.name());
#
# // Prints
# number
# of
# values
# of
# attribute
# "position"
# System.out.println("Number of values for \"position\": "
#                    + position.numValues());
#
# // Prints
# the
# values(againg)
# for (int i = 0; i < position.numValues(); i++) {
# System.out.println("Value " + i + ": " + position.value(i));
# }
#
# // Prints
# the
# attribute
# "position" in ARFF
# format
# System.out.println(position);
#
# // Checks
# type of attribute
# "position"
# using
# constants
# switch(position.type())
# {
#     case
# Attribute.NUMERIC: \
#     System.out.println("\"position\" is numeric");
# break;
# case
# Attribute.NOMINAL:
# System.out.println("\"position\" is nominal");
# break;
# case
# Attribute.STRING:
# System.out.println("\"position\" is string");
# break;
# case
# Attribute.DATE:
# System.out.println("\"position\" is date");
# break;
# case
# Attribute.RELATIONAL:
# System.out.println("\"position\" is relation-valued");
# break;
# default:
# System.out.println("\"position\" has unknown type");
# }
#
# ArrayList < Attribute > atts = new
# ArrayList < Attribute > (1);
# atts.add(position);
# Instances
# relation = new
# Instances("Test", atts, 0);
# Attribute
# relationValuedAtt = new
# Attribute("test", relation);
# System.out.println(relationValuedAtt);
# } catch(Exception
# e) {
#     e.printStackTrace();
# }
# }
# }
