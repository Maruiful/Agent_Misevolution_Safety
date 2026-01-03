package com.agent.misevolution.repository;

import com.agent.misevolution.domain.Experiment;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

/**
 * 实验数据访问层
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Mapper
public interface ExperimentMapper {

    /**
     * 插入实验记录
     *
     * @param params 实验参数（使用Map传递）
     * @return 影响行数
     */
    int insert(Map<String, Object> params);

    /**
     * 根据ID更新实验状态
     *
     * @param id 实验ID
     * @param status 新状态
     * @return 影响行数
     */
    int updateStatus(@Param("id") Long id, @Param("status") String status);

    /**
     * 更新当前轮次
     *
     * @param id 实验ID
     * @param currentEpisode 当前轮次
     * @return 影响行数
     */
    int updateCurrentEpisode(@Param("id") Long id, @Param("currentEpisode") Integer currentEpisode);

    /**
     * 实验完成时更新结束时间和状态
     *
     * @param id 实验ID
     * @param currentEpisode 最终轮次
     * @return 影响行数
     */
    int completeExperiment(@Param("id") Long id, @Param("currentEpisode") Integer currentEpisode);

    /**
     * 根据ID查询实验
     *
     * @param id 实验ID
     * @return 实验对象
     */
    Experiment selectById(@Param("id") Long id);

    /**
     * 根据UUID查询实验（通过experiment_name或其他标识）
     *
     * @param experimentName 实验名称
     * @return 实验对象
     */
    Experiment selectByName(@Param("experimentName") String experimentName);

    /**
     * 查询所有实验
     *
     * @return 实验列表
     */
    List<Experiment> selectAll();

    /**
     * 根据状态查询实验
     *
     * @param status 状态
     * @return 实验列表
     */
    List<Experiment> selectByStatus(@Param("status") String status);
}
