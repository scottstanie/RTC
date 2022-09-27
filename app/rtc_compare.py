'''
Compare two RTC products if they are equivalent
Part of the codes are copied from PROTEUS SAS
'''

import argparse
import itertools

import h5py
import numpy as np

RTC_S1_PRODUCTS_ERROR_TOLERANCE = 1e-6

def _get_parser():
    parser = argparse.ArgumentParser(
        description='Compare two DSWx-HLS products',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Inputs
    parser.add_argument('input_file',
                        type=str,
                        nargs=2,
                        help='Input RTC products in NETCDF/HDF5 format')

    return parser


def get_list_dataset_attrs_keys(hdf_obj_1, key_in='/',
                               list_dataset_so_far: list=None,
                               list_attrs_so_far: list=None):

    '''
    #TODO revise this docstring

    Recursively traverse the Dataset and Attributes in the 1st HDF5 (the reference).
    Try to find the same dataset in the 2nd HDF5 (the target).
    Returns 0 if the reference and the target HDF5 are identical within threshold
    Prints out the difference report when they are not.

    Paremeters:
    ----------
    hdf_obj_1: Reference HDF5 object
    hdf_obj_2: Target HDF5 object

    Return:
    -------
    _ : 0 if the two HDF are identical; 1 otherwise

    '''

    #default values for the lists
    if list_dataset_so_far is None:
        list_dataset_so_far = []
    if list_attrs_so_far is None:
        list_attrs_so_far = []

    if isinstance(hdf_obj_1[key_in], h5py.Group):
        for key_attr_1 in hdf_obj_1[key_in].attrs:
            #list_attrs_so_far.append([key_in, key_attr_1])
            list_attrs_so_far.append('\n'.join([key_in, key_attr_1]))

        for key_1, _ in hdf_obj_1[key_in].items():
            get_list_dataset_attrs_keys(hdf_obj_1, f'{key_in}/{key_1}',
                                        list_dataset_so_far,
                                        list_attrs_so_far)

    else:
        list_dataset_so_far.append(key_in)
        for key_attr_1 in hdf_obj_1[key_in].attrs:
            #list_attrs_so_far.append([key_in, key_attr_1])
            list_attrs_so_far.append('\n'.join([key_in, key_attr_1]))
    return list_dataset_so_far, list_attrs_so_far


def comapre_dataset_attr(hdf5_obj_1, hdf5_obj_2, str_key, is_attr=False):
    '''
    TODO: docstring please.

    Return:
    _: True when the dataset are identical; False otherwise
    '''
    if is_attr:
        path_attr, key_attr = str_key.split('\n')
        val_1 = hdf5_obj_1[path_attr].attrs[key_attr]
        val_2 = hdf5_obj_2[path_attr].attrs[key_attr]
        if not isinstance(val_1,np.ndarray):
            val_1 = np.array(val_1)

        if not isinstance(val_2,np.ndarray):
            val_1 = np.array(val_2)

    else:
        val_1=np.array(hdf5_obj_1[str_key])
        val_2=np.array(hdf5_obj_2[str_key])

    shape_val_1=np.array(val_1).shape
    shape_val_2=np.array(val_2).shape

    #if str_key=='//science/CSAR/RTC/grids/frequencyA/xCoordinates\nREFERENCE_LIST':
    #    print('Line for temporary breakpoint.')


    if not (shape_val_1 == shape_val_2):
        #print(f'Dataset or attribute shape does not match for key = {str_key}')
        return False

    elif len(shape_val_1)==0 and len(shape_val_2)==0:
        # Scalar value
        if val_1.dtype=='float' and val_2.dtype=='float':
            return np.array_equal(val_1, val_2, equal_nan=True)
        else:
            return np.array_equal(val_1, val_2)

    elif len(shape_val_1)==1 and len(shape_val_2)==1:
        # 1d vector
        if 'shape' in dir(val_1[0]):
            if isinstance(val_1[0], np.void):
                list_val_1=list(itertools.chain.from_iterable(val_1))
                val_1_new=[None]*len(list_val_1)
                for i_val, v in enumerate(list_val_1):
                    if isinstance(v, h5py.h5r.Reference):
                        val_1_new[i_val]=hdf5_obj_1[v]
                    else:
                        val_1_new[i_val]=v

                val_1=val_1_new

            elif (len(val_1[0].shape)==1) and (isinstance(val_1[0][0],h5py.h5r.Reference)):
                list_val_1=list(itertools.chain.from_iterable(val_1))
                #val_1_new=np.array([np.array(hdf5_obj_1[ref_val]) for ref_val in list_val_1])
                val_1_new=[None]*len(list_val_1)
                for i_val, v in enumerate(list_val_1):
                    if isinstance(v, h5py.h5r.Reference):
                        val_1_new[i_val]=hdf5_obj_1[v]
                    else:
                        val_1_new[i_val]=v
                val_1=val_1_new

        if 'shape' in dir(val_2[0]):
            if isinstance(val_2[0], np.void):
                list_val_2=list(itertools.chain.from_iterable(val_2))
                val_2_new=[None]*len(list_val_2)
                for i_val, v in enumerate(list_val_2):
                    if isinstance(v, h5py.h5r.Reference):
                        val_2_new[i_val]=hdf5_obj_2[v]
                    else:
                        val_2_new[i_val]=v

                val_2=val_2_new

            elif (len(val_2[0].shape)==1) and (isinstance(val_2[0][0],h5py.h5r.Reference)):
                list_val_2=list(itertools.chain.from_iterable(val_2))
                #val_2_new=np.array([hdf5_obj_1[ref_val] for ref_val in list_val_2])
                val_2_new=[None]*len(list_val_2)
                for i_val, v in enumerate(list_val_2):
                    if isinstance(v, h5py.h5r.Reference):
                        val_2_new[i_val]=hdf5_obj_2[v]
                    else:
                        val_2_new[i_val]=v

                val_2=val_2_new

        if isinstance(val_1, list) and isinstance(val_2, list):
            if len(val_1)==len(val_2):
                for id_element, element_1 in enumerate(val_1):
                    element_2=val_2[id_element]
                    if element_1.shape == element_2.shape:
                        if not np.allclose(element_1,element_2,RTC_S1_PRODUCTS_ERROR_TOLERANCE, equal_nan=True):
                            return False
                    else:
                        return False
                # Went through all elements in the list, and passed the closeness test in the for loop
                return True
            else:
                # List shape does not match
                return False
        
        elif val_1.dtype=='float' and val_2.dtype=='float':
            return np.array_equal(val_1, val_2, equal_nan=True)
        else:
            return np.array_equal(val_1, val_2)

    elif len(shape_val_1)>=2 and len(shape_val_2)>=2:
        #print('Single or multiband raster. shape:',hdf5_obj_1[key_dataset].shape)
        # TODO: Use compare_raster_dataset() to compare

        return np.allclose(val_1,
                           val_2,
                           RTC_S1_PRODUCTS_ERROR_TOLERANCE,
                           equal_nan=True)

    else:
        print('Detected an issue on the dataset shapes: ',
             f'Dataset key: {str_key}, '
              'dataset shape in the 1st HDF5: ', shape_val_1,
              'dataset shape in the 2nd HDF5: ', shape_val_2)
        return False


def main():
    '''
    Main function of the RTC comparison script
    - Compares the two HDF files by setting one of them as reference
    - Perform the same comparison abobe by settint the other HDF5 as reference
    '''
    parser = _get_parser()

    args = parser.parse_args()

    file_1 = args.input_file[0]
    file_2 = args.input_file[1]

    

    with h5py.File(file_1,'r') as hdf5_in_1, h5py.File(file_2,'r') as hdf5_in_2:
    #    compare_hdf5(hdf5_in_1, hdf5_in_2)
    #    compare_hdf5(hdf5_in_2, hdf5_in_1)
        list_dataset_1, list_attrs_1 = get_list_dataset_attrs_keys(hdf5_in_1)
        set_dataset_1 = set(list_dataset_1)
        set_attrs_1 = set(list_attrs_1)

        list_dataset_2, list_attrs_2 = get_list_dataset_attrs_keys(hdf5_in_2)
        set_dataset_2 = set(list_dataset_2)
        set_attrs_2 = set(list_attrs_2)


        # Check the dataset
        union_set_dataset = set_dataset_1.union(set_dataset_2)
        if len(union_set_dataset) == len(set_dataset_1) and \
           len(union_set_dataset) == len(set_dataset_2):
            print('\nDataset structure identical.')
            flag_identical_dataset_structure = True

        else:
            flag_identical_dataset_structure = False
            print('\nDataset structure not identical.')
            print('In the 1st HDF5, not in the 2nd data:')
            print('\n'.join(list(set_dataset_1 - set_dataset_2)))
            print('In the 2st HDF5, not in the 1nd data:')
            print('\n'.join(list(set_dataset_2 - set_dataset_1)))

        # Proceed with checking the values in dataset, regardless of the agreement of their structure.

        list_flag_identical_dataset = [None] * len(union_set_dataset)
        for id_flag, key_dataset in enumerate(union_set_dataset):
            list_flag_identical_dataset[id_flag] = comapre_dataset_attr(hdf5_in_1, hdf5_in_2, key_dataset, is_attr=False)
            if list_flag_identical_dataset[id_flag]:
                print(f'{id_flag+1:03d} / {len(union_set_dataset):03d} : PASSED. key: {key_dataset}')
            else:
                print(f'\033[91m{id_flag+1:03d} / {len(union_set_dataset):03d} : FAILED. key: {key_dataset}\033[00m')

        #"\033[91m {}\033[00m"

        # Check the attribute
        union_set_attrs = set_attrs_1.union(set_attrs_2)

        if len(union_set_attrs) == len(set_attrs_1) and \
           len(union_set_attrs) == len(set_attrs_2):
            flag_identical_attrs_structure = True
            print('\nAttribute structure identical.')


        else:
            flag_identical_attrs_structure = False
            print('\nAttribute structure not identical.')
            print('In the 1st HDF5, not in the 2nd data:')
            print('\n'.join(list(set_dataset_1 - set_dataset_2)))
            print('In the 2st HDF5, not in the 1nd data:')
            print('\n'.join(list(set_dataset_2 - set_dataset_1)))

        # Proceed with checking the values in dataset, regardless of the agreement of their structure.

        list_flag_identical_attrs = [None] * len(union_set_attrs)
        for id_flag, key_attr in enumerate(union_set_attrs):
            list_flag_identical_attrs[id_flag] = comapre_dataset_attr(hdf5_in_1, hdf5_in_2, key_attr, is_attr=True)
            str_printout=key_attr.replace('\n',' - ')
            if list_flag_identical_attrs[id_flag]:
                print(f'{id_flag+1:03d} / {len(union_set_attrs):03d} : PASSED. path - key: {str_printout}')
            else:
                print(f'\033[91m{id_flag+1:03d} / {len(union_set_attrs):03d} : FAILED. path - key: {str_printout}\033[00m')



        # Print out the test summary:
        print('\n\n****************** Test summary ******************')
        print(f'1st HDF FILE                 : {file_1}')
        print(f'2nd HDF FILE                 : {file_2}')
        print(f'Value tolerance              : {RTC_S1_PRODUCTS_ERROR_TOLERANCE}')
        print(f'\nIdentical dataset structure  : {flag_identical_dataset_structure}')
        print(f'Identical Attribute structure: {flag_identical_attrs_structure}\n')

        if all(list_flag_identical_dataset):
            print('All dataset passed the test')
        else:
            print('Dataset below did not pass the test:')
            for id_dataset, key_dataset in enumerate(union_set_dataset):
                if not list_flag_identical_dataset[id_dataset]:
                    print(key_dataset)

        if all(list_flag_identical_attrs):
            print('All attributes passed the test')
        else:
            print('\nAttributes below did not pass the test:')
            for id_attr, key_attr in enumerate(union_set_attrs):
                if not list_flag_identical_attrs[id_attr]:
                    token_key_attr=key_attr.split('\n')
                    print(f'{token_key_attr[1]} {token_key_attr[0]}')





if __name__ == '__main__':
    main()
